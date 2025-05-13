from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from pydantic import BaseModel
import requests
import random
import math
import time
import json
import ast
import os
import re

from cha import scraper, colors, utils, config, loading


def create_mega_prompt(search_results, prompt):
    return utils.rls(
        f"""
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
    )


def generate_search_queries(
    client, user_prompt, model_name, min_results=config.DEFAULT_GEN_SEARCH_QUERY_COUNT
):
    prompt = utils.rls(
        f"""
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
    )

    if config.CHA_CURRENT_PLATFORM_NAME == "openai":
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
    else:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        response = response.choices[0].message.content

        # NOTE: regex to match content inside square brackets (simple, may need refinement for nested/complex cases)
        list_candidates = re.findall(r"\[[^\]]*\]", response)

        extracted_lists = []
        for candidate in list_candidates:
            try:
                parsed_value = ast.literal_eval(candidate.strip())
                if isinstance(parsed_value, list):
                    extracted_lists.append(parsed_value)
            except (SyntaxError, ValueError):
                continue

        output = []
        for entry in extracted_lists:
            for query in entry:
                if query not in output:
                    output.append(query)

        random.shuffle(output)

        if len(output) == 0:
            print(
                colors.red(
                    "Failed to generate search queries just using user's original prompt"
                )
            )
            return [user_prompt]

        return output[:min_results]


def search_engine(
    search_input, count=5, region="wt-wt", safesearch="off", timelimit=None
):
    try:
        searxng_base_url = str(config.CHA_SEAR_XNG_BASE_URL)
        searxng_running = True

        if config.CHA_USE_SEAR_XNG == True and "http" in searxng_base_url:
            try:
                response = requests.get(
                    searxng_base_url,
                    timeout=max(math.ceil(config.CHA_SEAR_XNG_TIMEOUT / 10), 1),
                )
                if response.status_code != 200:
                    searxng_running = False
            except requests.ConnectionError:
                searxng_running = False
            except requests.Timeout:
                searxng_running = False

        if (
            config.CHA_USE_SEAR_XNG == True
            and searxng_running == True
            and "http" in searxng_base_url
        ):
            response = requests.get(
                searxng_base_url.rstrip("/") + "/search",
                params={"q": search_input, "format": "json"},
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
                timeout=config.CHA_SEAR_XNG_TIMEOUT,
            )

            response.raise_for_status()
            response = response.json()

            content = []
            for result in response["results"]:
                content.append(
                    {
                        "title": result.get("title"),
                        "url": result.get("url"),
                        "description": result.get("content"),
                    }
                )

            return content[:count]

        from duckduckgo_search import DDGS

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
        print(e)
        return {"error": str(e)}


def quick_search(user_input, min_search_result=3):
    try:
        results = search_engine(
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

        return utils.rls(
            f"""
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
            """
        )
    except:
        return None


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
        if prompt == config.TEXT_EDITOR_INPUT_MODE.strip():
            editor_content = utils.check_terminal_editors_and_edit()
            if editor_content is None or len(editor_content) < 5:
                prompt = utils.safe_input(
                    colors.red("[retrying] ") + colors.blue(f"Question: ")
                )
            else:
                for line in str(editor_content).rstrip("\n").split("\n"):
                    print(colors.blue(">"), line)
                prompt = editor_content
    else:
        print(colors.red(colors.underline("Question Prompt:")))
        print(prompt)

    loading.start_loading("Crafting Queries", "circles")

    search_queries = generate_search_queries(client, prompt, small_model)

    loading.stop_loading()

    print(colors.red(colors.underline("Search Queries:")))
    for url in search_queries:
        print(colors.yellow(f"- {url}"))

    loading.start_loading("Browsing", "circles")

    search_results = []
    urls = []
    for query in search_queries:
        results = search_engine(query, result_count)

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
