from datetime import datetime, timezone
from pydantic import BaseModel
import requests
import time
import json
import os

from cha import scraper, colors, utils, config


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
    system_prompt = f"""
You are a helpful assistant that generates three distinct search engine queries from a user's prompt.
These search engine queries are optimized towards getting the best results that can best answer the user's prompt
Each query should be optimized to capture different aspects or angles of the user's intent.
Format the output strictly as an array of strings.
Make sure to provide ATLEAST {min_results} good search engine queries.
Also note, today's date in ISO 8601 format is: {datetime.now(timezone.utc).isoformat()}
    """

    # NOTE: this insures the output is always an array of strings as it should be
    class SearchQueries(BaseModel):
        queries: list[str]

    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        response_format=SearchQueries,
    )

    return completion.choices[0].message.parsed.queries


def brave_search(
    search_input,
    count=3,
    freshness="none",
    result_filter=None,
):
    if freshness not in list(config.VALID_FRESHNESS_IDS.keys()):
        raise Exception(f"Freshness '{freshness}' is NOT a valid freshness id")

    if result_filter == None or type(result_filter) != str:
        result_filter = "web,news,query,infobox,discussions"

    # setup Brave API key: https://api.search.brave.com/app/dashboard
    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": os.environ.get("BRAVE_API_KEY"),
        },
        params={
            # (required) the user's search query term
            "q": search_input,
            # (optional) the search query country
            "country": "us",
            # (optional) the search language preference
            "search_lang": "en",
            # (optional) user interface language preferred in response
            "ui_lang": "en-US",
            # (optional) the number of search results returned in response
            "count": count,
            # (optional) the zero-based offset for pagination
            "offset": 0,
            # (optional) filters search results for adult content
            "safesearch": "off",
            # (optional) filters search results by when they were discovered
            "freshness": freshness,
            # (optional) specifies if text decorations should be applied
            "text_decorations": 1,
            # (optional) specifies if spellcheck should be applied
            "spellcheck": 1,
            # (optional) a comma-delimited string of result types to include
            "result_filter": result_filter,
        },
    )

    search_results = response.json()

    # simplify final output for our needs
    try:
        if search_results.get("type") == "ErrorResponse":
            raise Exception(str(search_results.get("error")))
        search_results = search_results["web"]["results"]
        content = []
        for result in search_results:
            content.append(
                {
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "description": result.get("description"),
                    "page_age": result.get("page_age"),
                    "age": result.get("age"),
                }
            )
        return content
    except Exception as e:
        return {"error": e}


def answer_search(
    client,
    prompt=None,
    big_model=config.DEFAULT_SEARCH_BIG_MODEL,
    small_model=config.DEFAULT_SEARCH_SMALL_MODEL,
    result_count=config.DEFAULT_SEARCH_RESULT_COUNT,
    freshness_state=config.DEFAULT_SEARCH_FRESHNESS_STATE,
    time_delay_seconds=config.DEFAULT_SEARCH_TIME_DELAY_SECONDS,
    token_limit=config.DEFAULT_SEARCH_MAX_TOKEN_LIMIT,
    user_input_mode=False,
):
    if user_input_mode or prompt == None:
        print(colors.red(colors.underline(f"Answer Search - User Input")))

        prompt = utils.safe_input(colors.blue(f"Question: "))

        freshness_state = utils.safe_input(
            colors.blue(
                "Freshness:"
                + "".join(
                    f"\n- {f} = {config.VALID_FRESHNESS_IDS[f]}"
                    for f in config.VALID_FRESHNESS_IDS
                )
                + "\n> "
            )
        )
        if len(freshness_state) == 0:
            freshness_state = "none"

        filters = config.SEARCH_FILTER_OPTIONS

    search_queries = generate_search_queries(client, prompt, small_model)

    print(colors.red(colors.underline("Search Queries:")))
    for url in search_queries:
        print(colors.yellow(f"- {url}"))

    search_results = []
    urls = []
    for query in search_queries:
        results = brave_search(query, result_count, freshness_state, filters)

        # TODO: this is here to prevent us from surpassing Brave's query limit
        time.sleep(time_delay_seconds)

        if isinstance(results, dict) and "error" in results:
            continue

        for result in results:
            url = result.get("url")
            if url and not any(existing["url"] == url for existing in search_results):
                search_results.append(result)
                urls.append(url)

    print(colors.red(colors.underline(f"Search Query Results ({len(urls)} Total):")))
    for url in urls:
        print(colors.yellow(f"- {url}"))

    print(colors.red(colors.underline("Scraping Website Content:")))
    scrapped_data = scraper.get_all_htmls(urls)
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

    print(colors.red(colors.underline("Response:")))

    response = client.chat.completions.create(
        model=big_model,
        messages=[{"role": "user", "content": mega_prompt}],
        stream=True,
    )

    final_output = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            final_output += content
            print(colors.green(content), end="", flush=True)

    if final_output.endswith("\n") == False:
        print()

    return final_output
