from contextlib import redirect_stdout, redirect_stderr
import time
import json
import os

from cha import scraper, colors, utils, config, loading, answer


def quick_search(user_input, min_search_result=3):
    results = answer.duckduckgo_search(
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
```
{str(output)}
```

Knowing this context and your own internal knowledge, please answer the user's prompt/question as best as you can.
""".strip()


if __name__ == "__main__":
    user_input = input("Question: ")

    start_time = time.time()

    output = quick_search(user_input)

    runtime = time.time() - start_time

    print("Output:")
    print("===============")
    print(output)
    print("===============")
    print()
    print("Tokens:", utils.count_tokens(str(output), "gpt-4o"))
    print(f"Runtime: {runtime} seconds")
