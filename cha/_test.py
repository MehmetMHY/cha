from contextlib import redirect_stdout, redirect_stderr
import time
import json
import os

from cha import scraper, colors, utils, config, loading, answer

if __name__ == "__main__":
    from openai import OpenAI
    import random

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    user_input = input("Question: ")

    start_time = time.time()

    search_loop_delay_secs = 0.1
    default_model = "gpt-4o-mini"
    min_search_result = 3
    default_result_count = 2
    time_limit_options = ["none", "y", "m", "w", "d"]
    i = 0

    search_params = answer.generate_search_queries(
        client=client,
        user_prompt=user_input,
        model_name=default_model,
        min_results=min_search_result,
    )

    random.shuffle(search_params)

    search_results = {}
    urls = []
    for query_text in search_params:
        query = {
            "search_input": query_text,
            "count": default_result_count,
            "region": "wt-wt",
            "safesearch": "off",
            "timelimit": time_limit_options[i],
        }

        results = answer.duckduckgo_search(
            search_input=query["search_input"],
            count=query["count"],
            region=query["region"],
            safesearch=query["safesearch"],
            timelimit=query["timelimit"],
        )

        if isinstance(results, dict) and "error" in results:
            continue

        for result in results:
            url = str(result["url"])
            if url not in urls:
                urls.append(url)
            search_results[url] = result

        i += 1
        time.sleep(search_loop_delay_secs)

    # TODO: suppress all untraceable print statements by muting all stdout prints
    with open(os.devnull, "w") as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            scrapped_data = scraper.get_all_htmls(urls)

    output = []
    for url in scrapped_data:
        if url in search_results:
            search_results[url]["content"] = scrapped_data[url]
            output.append(search_results[url])

    runtime = time.time() - start_time

    print("Output:")
    print(json.dumps(output, indent=4))

    token_count = utils.count_tokens(str(output), "gpt-4o")
    print(f"Token Count: {token_count}")
    print(f"Runtime: {runtime} seconds")
