from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from pydantic import BaseModel
import concurrent.futures
import time
import json
import os

from cha import scraper, colors, utils, config, loading
from duckduckgo_search import DDGS


def create_mega_prompt(search_results, prompt, is_final=False):
    mega_prompt = f"""
For your answer, understand that today's date is: {datetime.now(timezone.utc).isoformat()}

Here is some additional context that may be useful:
```json
{json.dumps(search_results)}
```

Please answer the following question using both your existing knowledge and the context provided above:
```
{prompt}
```

Instructions:
1. Integrate your own knowledge with the context provided.
2. Reference relevant information from the context above where appropriate.
3. Include inline citations using square brackets, e.g., [1], in IEEE format for any referenced content. Do not include anything else (url, title, description, etc).
4. Make sure there is a space between a word and the referenced content. Meaning, "word[1]" is NOT ok, rather it should be "word [1]"
5. Ensure all citations contain a URL and are formatted correctly.
6. Present your final answer as plain text, without using Markdown-specific tags or formatting (e.g., no ```markdown, or similar tags).

IEEE Citation Format Example:
- [1] Author(s), "Article Title," *Journal Title*, vol. number, no. number, pp. pages, Month, Year. [Online]. Available: URL

Make sure to clearly refer to each citation in the body of your response. Your answer should be clear, concise, and well-structured!
"""

    if is_final:
        mega_prompt = (
            "NOTE: This process/prompting was already done many times and this is the final prompt/request to answer the user's question. For context, the results from all the sub-answer processes was included.\n\n"
            + mega_prompt
        )

    return mega_prompt


def generate_search_queries(
    client, user_prompt, model_name, min_results=config.DEFAULT_GEN_SEARCH_QUERY_COUNT
):
    prompt = f"""
Today's date, in ISO 8601 format, is: {datetime.now(timezone.utc).isoformat()}.

Your task is to generate at least {min_results} distinct search engine queries based on the user's prompt provided below:
```md
{user_prompt}
```

Instructions:
1. Create search engine queries that extract the most relevant results for the user's prompt.
2. Ensure each query is optimized to explore different aspects or angles of the user's intent.
3. Format the queries as an array of strings.

Example Format:
- ["Query 1", "Query 2", "Query 3"]
"""

    # NOTE: this insures the output is always an array of strings as it should be
    class SearchQueries(BaseModel):
        queries: list[str]

    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format=SearchQueries,
    )

    return completion.choices[0].message.parsed.queries


def duckduckgo_search(
    search_input, count=5, region="wt-wt", safesearch="off", timelimit=None
):
    try:
        with DDGS() as ddgs:
            search_results = list(
                ddgs.text(
                    keywords=search_input,
                    max_results=count,
                    region=region,
                    safesearch=safesearch,
                    timelimit=timelimit,
                )
            )

            content = []
            for result in search_results:
                content.append(
                    {
                        "title": result.get("title"),
                        "url": result.get("href"),
                        "description": result.get("body"),
                    }
                )

            return content
    except Exception as e:
        return {"error": str(e)}


def chunk_list(lst, n):
    # split list into n (almost) equal chunks
    k, m = divmod(len(lst), n)
    chunks = []
    start = 0
    for i in range(n):
        size = k + (1 if i < m else 0)
        chunk = lst[start : start + size]
        start += size
        if chunk:
            chunks.append(chunk)
    return chunks


def get_partial_answer(client, big_model, sub_search_results, user_prompt):
    sub_mega_prompt = create_mega_prompt(sub_search_results, user_prompt)
    response = client.chat.completions.create(
        model=big_model,
        messages=[{"role": "user", "content": sub_mega_prompt}],
        stream=False,  # do not stream partial calls
    )
    partial_output = ""
    for choice in response.choices:
        if choice.message.content:
            partial_output += choice.message.content
    return partial_output


def answer_search(
    client,
    prompt=None,
    big_model=config.DEFAULT_SEARCH_BIG_MODEL,
    small_model=config.DEFAULT_SEARCH_SMALL_MODEL,
    result_count=config.DEFAULT_SEARCH_RESULT_COUNT,
    time_delay_seconds=config.DEFAULT_SEARCH_TIME_DELAY_SECONDS,
    token_limit=config.DEFAULT_SEARCH_MAX_TOKEN_LIMIT,
    user_input_mode=False,
    fast_token_count_mode=False,
):
    if user_input_mode or prompt == None:
        print(colors.red(colors.underline(f"Answer Search - User Input")))
        prompt = utils.safe_input(colors.blue(f"Question: "))
        if prompt.lower() == config.TEXT_EDITOR_INPUT_MODE.lower():
            prompt = utils.check_terminal_editors_and_edit()
            if prompt is None:
                print(colors.red(f"No text editor available or editing cancelled"))
                return
            if len(prompt) > 0:
                for line in prompt.rstrip("\n").split("\n"):
                    print(colors.blue(">"), line)
            else:
                print(colors.red("Nothing was entered into the text editor"))
                return
    else:
        print(colors.red(colors.underline("Question Prompt:")))
        print(prompt)

    search_queries = generate_search_queries(client, prompt, small_model)

    print(colors.red(colors.underline("Search Queries:")))
    for url in search_queries:
        print(colors.yellow(f"- {url}"))

    loading.start_loading("Browsing", "circles")

    # NOTE: the time/age limit options for the search results
    time_limit_options = ["none", "y", "m", "w", "d"]

    search_results = []
    urls = []
    i = 0
    for query in search_queries:
        if i >= len(time_limit_options):
            i = 0

        results = duckduckgo_search(
            search_input=query, count=result_count, timelimit=time_limit_options[i]
        )

        # prevent surpassing rate limit
        time.sleep(time_delay_seconds)

        if isinstance(results, dict) and "error" in results:
            continue

        for result in results:
            url = result.get("url")
            if url and not any(existing["url"] == url for existing in search_results):
                search_results.append(result)
                urls.append(url)

        i += 1

    loading.stop_loading()

    # TODO: this solution sucks, but scraping videos can take minutes to process or even lead to a crash
    not_video_urls = [
        url
        for url in urls
        if not url.startswith(tuple(config.VALID_VIDEO_ROOT_URL_DOMAINS_FOR_SCRAPING))
    ]
    if len(not_video_urls) == 0:
        # TODO: this solution really sucks, we need to build a better solution for this edge case
        print(colors.red(f"zero non-video based urls were founded"))
        return ""

    print(colors.red(colors.underline(f"Search Query Results ({len(urls)} Total):")))
    for url in urls:
        if url not in not_video_urls:
            print(colors.yellow(f"x {url}"))
        else:
            print(colors.yellow(f"- {url}"))

    print(colors.red(colors.underline("Scraping Website Content:")))
    loading.start_loading("Scraping", "circles")

    # TODO: suppress all untraceable print statements by muting all stdout prints
    with open(os.devnull, "w") as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            scrapped_data = scraper.get_all_htmls(not_video_urls)

    for url in scrapped_data:
        for entry in search_results:
            if url == entry["url"]:
                entry["content"] = scrapped_data[url]

    loading.stop_loading()
    print(colors.yellow(f"Scraped {len(scrapped_data)}/{len(urls)} of the urls"))

    print(colors.red(colors.underline("Generating Sub Answers:")))
    loading.start_loading("Processing", "vertical_bar")

    if len(search_results) <= config.DEFAULT_SPLIT_LOGIC_COUNT:
        splitted_search_results = [search_results]
    else:
        splitted_search_results = chunk_list(
            search_results, config.DEFAULT_SPLIT_LOGIC_COUNT
        )

    partial_answers = []
    if len(splitted_search_results) == 1:
        partial_answers.append(
            get_partial_answer(client, big_model, splitted_search_results[0], prompt)
        )
    else:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(splitted_search_results)
        ) as executor:
            total = len(splitted_search_results)
            futures = [
                executor.submit(get_partial_answer, client, big_model, chunk, prompt)
                for chunk in splitted_search_results
            ]
            done_count = 0
            for f in concurrent.futures.as_completed(futures):
                partial_answers.append(f.result())
                done_count += 1
                loading.print_message(
                    colors.yellow(f"Generated sub-answer {done_count}/{total}")
                )

    loading.stop_loading()

    mega_prompt = create_mega_prompt(partial_answers, prompt)
    print(colors.red(colors.underline("Check Final Prompt Limit:")))
    removed_sub_answer_count = 0
    while (
        utils.count_tokens(
            text=mega_prompt, model_name=big_model, fast_mode=fast_token_count_mode
        )
        >= token_limit
    ):
        for entry in search_results:
            partial_answers = partial_answers[:-1]
            removed_sub_answer_count += 1
            mega_prompt = create_mega_prompt(partial_answers, prompt)
            break
    print(
        colors.yellow(
            f"Removed {removed_sub_answer_count} sub-answers to fit within the model's context window limit"
        )
    )

    final_output = ""
    try:
        print(colors.red(colors.underline("Final Response:")))

        loading.start_loading("Crafting", "circles")

        response = client.chat.completions.create(
            model=big_model,
            messages=[{"role": "user", "content": mega_prompt}],
            stream=True,
        )

        received_first_chunk = False
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                if not received_first_chunk:
                    loading.stop_loading()
                    received_first_chunk = True

                content = chunk.choices[0].delta.content
                final_output += content
                print(colors.green(content), end="", flush=True)

        if final_output.endswith("\n") == False:
            print()
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        loading.stop_loading()

    return final_output


def quick_search(user_input, min_search_result=3):
    try:
        results = duckduckgo_search(
            search_input=user_input,
            count=min_search_result,
            region="wt-wt",
            safesearch="off",
            timelimit="none",
        )

        urls = []
        for result in results:
            url = str(result["url"])
            if url not in urls:
                urls.append(url)

        # TODO: suppress all untraceable print statements by muting all stdout prints
        with open(os.devnull, "w") as fnull:
            with redirect_stdout(fnull), redirect_stderr(fnull):
                scrapped_data = scraper.get_all_htmls(urls)

        output = []
        for result in results:
            url = str(result["url"])
            description = str(result.get("description"))
            content = None
            if url in scrapped_data:
                content = str(scrapped_data[url])
            if content == None or len(description) >= len(content):
                content = str(description)
            output.append({"url": url, "content": content})

        return f"""
Here is the user's prompt/question:
```
{user_input}
```

Here is some context extracted from the internet:
```json
{output}
```

Instructions:
1. Use your own knowledge and the context provided above to answer the question.
2. Reference relevant information from the context above where appropriate.
3. Include inline citations using square brackets, e.g., [1], formatted in IEEE style for any referenced content.
4. Ensure all citations contain a URL and are formatted correctly.
5. Present your final answer as plain text, without using Markdown-specific tags or formatting.

Your answer should be clear, concise, and well-structured!
""".strip()
    except:
        return None
