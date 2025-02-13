from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from duckduckgo_search import DDGS
from pydantic import BaseModel
import time
import json
import os

from cha import scraper, colors, utils, config, loading


def create_mega_prompt(search_results, prompt):
    mega_prompt = f"""
For your answer, understand that today's date is: {datetime.now(timezone.utc).isoformat()}

Here is some additional context that may be useful:
```json
{json.dumps(search_results)}
```

Please answer the following question using both your existing knowledge and the context provided above:
```md
{prompt}
```

Instructions:
1. Integrate your own knowledge with the context provided.
2. Reference relevant information from the context above where appropriate.
3. Include inline citations using square brackets, e.g., [1], in IEEE format for any referenced content. Do not include anything else (url, title, description, etc).
4. Make sure there is a space between a word and the referenced content. Meaning, "word[1]" is NOT ok, rather it should be "word [1]"
5. Ensure all citations contain a URL and are formatted correctly.
6. Present your final answer in markdown format.

IEEE Citation Format Example:
- [1] Author(s), "Article Title," *Journal Title*, vol. number, no. number, pp. pages, Month, Year. [Online]. Available: URL

Make sure to clearly refer to each citation in the body of your response. Your answer should be clear, concise, and well-structured!
"""
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


def duckduckgo_search(search_input, count=3):
    try:
        with DDGS() as ddgs:
            search_results = list(
                ddgs.text(
                    keywords=search_input,
                    max_results=count,
                    region="wt-wt",  # NOTE: this is equivalent to Brave's {'country': 'us'}
                )
            )

            content = []
            for result in search_results:
                content.append(
                    {
                        "title": result.get("title"),
                        "url": result.get("href"),
                        "description": result.get("body"),
                        "page_age": None,
                        "age": None,
                    }
                )

            return content
    except Exception as e:
        return {"error": str(e)}


def answer_search(
    client,
    prompt=None,
    big_model=config.DEFAULT_SEARCH_BIG_MODEL,
    small_model=config.DEFAULT_SEARCH_SMALL_MODEL,
    result_count=config.DEFAULT_SEARCH_RESULT_COUNT,
    time_delay_seconds=config.DEFAULT_SEARCH_TIME_DELAY_SECONDS,
    token_limit=config.DEFAULT_SEARCH_MAX_TOKEN_LIMIT,
    user_input_mode=False,
):
    if user_input_mode or prompt == None:
        print(colors.red(colors.underline(f"Answer Search - User Input")))
        prompt = utils.safe_input(colors.blue(f"Question: "))
    else:
        print(colors.red(colors.underline("Question Prompt:")))
        print(prompt)

    search_queries = generate_search_queries(client, prompt, small_model)

    print(colors.red(colors.underline("Search Queries:")))
    for url in search_queries:
        print(colors.yellow(f"- {url}"))

    loading.start_loading("Browsing", "circles")

    search_results = []
    urls = []
    for query in search_queries:
        results = duckduckgo_search(query, result_count)

        # TODO: this is here to prevent us from surpassing the search engine's query limit
        time.sleep(time_delay_seconds)

        if isinstance(results, dict) and "error" in results:
            continue

        for result in results:
            url = result.get("url")
            if url and not any(existing["url"] == url for existing in search_results):
                search_results.append(result)
                urls.append(url)

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
    # TODO: suppress all untrackable print statements by muting all stdout prints
    with open(os.devnull, "w") as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            scrapped_data = scraper.get_all_htmls(not_video_urls)
    loading.stop_loading()

    for url in scrapped_data:
        for entry in search_results:
            if url == entry["url"]:
                entry["content"] = scrapped_data[url]
    print(colors.yellow(f"Scraped {len(scrapped_data)}/{len(urls)} of the urls"))

    # TODO: this solution sucks, but it works and prevents us from exceeding the prompt limit
    mega_prompt = create_mega_prompt(search_results, prompt)
    print(colors.red(colors.underline("Check Final Prompt Limit:")))
    cleared_urls = []
    current_prompt_size = utils.count_tokens(mega_prompt, big_model)
    if current_prompt_size < token_limit:
        print(
            colors.yellow(
                f"Final prompt does not exceed model's limit of {token_limit} tokens"
            )
        )
    else:
        print(
            colors.yellow(
                f"Final prompt exceeds model's limit of {token_limit} tokens ({current_prompt_size})"
            )
        )
        while utils.count_tokens(mega_prompt, big_model) >= token_limit:
            for entry in search_results:
                if type(entry.get("content")) == str:
                    url = entry.get("url")
                    entry["content"] = None
                    cleared_urls.append(url)
                    mega_prompt = create_mega_prompt(search_results, prompt)
                    print(colors.yellow(f"Cleared scraped content for {url}"))
                    break

    final_output = ""
    try:
        print(colors.red(colors.underline("Response:")))

        loading.start_loading("Crafting", "circles")

        response = client.chat.completions.create(
            model=big_model,
            messages=[{"role": "user", "content": mega_prompt}],
            stream=True,
        )

        received_first_chunk = False
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                # stop loading animation after stream starts
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
