import concurrent.futures
import requests
import json
import time
import ast
import sys
import os
import re

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import tiktoken
import openai

from cha import scraper, colors, config

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def generate_search_results(question, model, time_delay=1.5):
    prompt = f"Response to the following question as a JSON (array of strings). Question: Given a complex prompt, decompose it into multiple simpler search engine queries. Complex Prompt: {question}"

    response = client.chat.completions.create(
        model=model, messages=[{"role": "system", "content": prompt}]
    )

    queries = ast.literal_eval(response.choices[0].message.content)
    queries.append(question)

    results = {}
    for query in list(set(queries)):
        try:
            time.sleep(time_delay)

            search = config.brave_search(query)

            results[query] = {"query": search["query"]["original"], "pages": []}

            for page in search["web"]["results"]:
                results[query]["pages"].append(
                    {
                        "title": page["title"],
                        "url": page["url"],
                        "age": page.get("page_age"),
                    }
                )
        except:
            pass

    return {"prompt": prompt, "results": results}


def get_sources(query):
    try:
        response = generate_search_results(query, config.cheap_model, 2.0)
        return response
    except Exception as err:
        return None


def token_count(model_name: str, string: str) -> int:
    encoding_name = tiktoken.encoding_for_model(model_name)
    encoding = tiktoken.get_encoding(encoding_name.name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def adjust_prompt_to_token_limit(model, prompt: str, token_limit: int) -> str:
    num_tokens = token_count(model, prompt)
    while num_tokens > token_limit and token_limit >= 0:
        diff = int((num_tokens - config.cheap_model_max_token) / 2)
        if diff == 0:
            diff = 1
        prompt = prompt[:-(diff)]
        num_tokens = token_count(model, prompt)
    return prompt


def convert_search_results(search_results):
    for key in search_results:
        pages_list = search_results[key]["pages"]
        url_dict = {}
        for page in pages_list:
            url = page.get("url")
            if url:
                page_info = {k: v for k, v in page.items()}
                url_dict[url] = page_info
                url_dict[url]["content"] = ""
        search_results[key]["pages"] = url_dict
    return search_results


def is_valid_url(url):
    # check if the URL ends with any of the excluded extensions
    if any(url.lower().endswith(ext) for ext in config.excluded_extensions):
        return False

    # match common file naming conventions on the web; likely non-HTML content
    patterns = config.invalid_url_patterns
    if any(re.search(pattern, url, re.IGNORECASE) for pattern in patterns):
        return False

    return True


def convert_all_urls(search_results):
    # merge all url lists into one list
    all_urls = []
    for key in search_results:
        all_urls += search_results[key]["pages"].keys()

    # filter by only valid urls
    final_urls = []
    for url in all_urls:
        if is_valid_url(url):
            final_urls.append(url)

    return list(set(final_urls))


def scrape_html(url, headless=True, time_delay=10):
    options = webdriver.ChromeOptions()
    if headless:
        # run Chrome in headless mode
        options.add_argument("--headless")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )

    try:
        driver.get(url)

        # wait for page to load
        time.sleep(time_delay)

        return driver.page_source
    finally:
        driver.quit()


def scrape_urls_in_parallel(urls, max_workers=10):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_html, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_content = future.result()
                results[url] = html_content
            except Exception as exc:
                # print(f"Error for {url}: {exc}")
                results[url] = None
    return results


def summarize_urls_data(scraped_url_data):
    sum_scraped_url_data = {}

    for key in scraped_url_data:
        response = None
        try:
            prompt = f"Summarize the following text into one paragraph:\n```\n{scraped_url_data[key]}\n```"
            prompt = adjust_prompt_to_token_limit(
                config.cheap_model, prompt, config.cheap_model_max_token
            )
            response = (
                client.chat.completions.create(
                    model=config.cheap_model,
                    messages=[{"role": "system", "content": prompt}],
                )
                .choices[0]
                .message.content
            )
        except:
            pass

        sum_scraped_url_data[key] = response

    return sum_scraped_url_data


def research_prompt(url_data, question):
    source_ids = {}

    # build the main prompt
    prompt = "Given the following research (source & notes):\n```\n"
    i = 1
    for key in url_data:
        source_ids[i] = key
        content = url_data[key].replace("\n", " ")
        prompt += f"{i}) {key} : {content}\n\n"
        i += 1
    prompt = prompt.rstrip("\n") + "\n```\n\n"
    prompt += f"Answer the following question (make sure to site the sources by JUST using their respected number/id):\n```\n{question}\n```"

    return {"prompt": prompt, "ids": source_ids}


def answer_search(user_question, print_mode=False):
    if "OPENAI_API_KEY" not in os.environ and "BRAVE_API_KEY" not in os.environ:
        print(
            colors.red(
                f"Can't run advance-search, the OPENAI_API_KEY & BRAVE_API_KEY environment variables are NOT defined"
            )
        )
        return None

    output = {
        "all_urls": [],
        "scraped_urls": [],
        "runtime": 0,
        "search_queries": [],
        "models": {
            "small": {"name": config.cheap_model, "tokens": 0},
            "large": {"name": config.big_model, "tokens": 0},
        },
        "search_results": {},
        "output": {"question": user_question, "sources": {}, "answer": ""},
    }

    if print_mode:
        print(colors.green("Question: ") + str(user_question))
        print()

    start_time = time.time()

    # gather search browser results/data
    raw_search_results = get_sources(user_question)
    search_results = raw_search_results["results"]
    search_results = convert_search_results(search_results)

    output["models"]["small"]["tokens"] += token_count(
        config.cheap_model, raw_search_results["prompt"]
    )
    output["search_results"] = search_results
    output["search_queries"] = list(search_results.keys())

    if print_mode:
        print(colors.green(f"Sub-Questions:"))
        for i in output["search_queries"]:
            print(f"- {i}")
        print()
        print(colors.green(f"Started web scraping..."))
        print()

    # scrape all webpages rathered from the browser
    all_urls = convert_all_urls(search_results)
    raw_scraped_url_data = scrape_urls_in_parallel(all_urls)
    scraped_url_data = {}
    for url in raw_scraped_url_data:
        if raw_scraped_url_data[url] != None:
            scraped_url_data[url] = scraper.remove_html(raw_scraped_url_data[url])

    output["all_urls"] = all_urls
    output["scraped_urls"] = scraped_url_data

    if print_mode:
        print(colors.green(f"Total Websites/URLs: ") + str(len(output["all_urls"])))
        print(
            colors.green(f"Total Processed URLs: ")
            + str(len(list(output["scraped_urls"].keys())))
        )
        print()

    # reduce token count by summarizing a lot of the results
    output["models"]["small"]["tokens"] += token_count(
        config.cheap_model, str(scraped_url_data)
    )
    scraped_url_data = summarize_urls_data(scraped_url_data)
    output["models"]["small"]["tokens"] += token_count(
        config.cheap_model, str(scraped_url_data)
    )

    if print_mode:
        print(colors.green("Finished summarizing scarpped content"))
        print()

    # create main prompt for big model
    prompt_data = research_prompt(scraped_url_data, user_question)
    prompt = prompt_data["prompt"]
    source_ids = prompt_data["ids"]

    # (print mode) send final prompt to the big model
    final_response = ""
    if print_mode:
        print(colors.blue("=======Bibliography=======\n"))
        for i in source_ids:
            print(colors.yellow(f"{i}) {source_ids[i]}"))

        print(colors.blue("\n========CONCLUSION========\n"))

        response = client.chat.completions.create(
            model=config.big_model,
            messages=[{"role": "system", "content": prompt}],
            stream=True,
        )

        for chunk in response:
            chunk_message = chunk.choices[0].delta.content
            final_response += final_response
            if chunk_message:
                sys.stdout.write(colors.green(chunk_message))
                sys.stdout.flush()

    # (none print mode) send final prompt to the big model
    if print_mode == False:
        final_response = (
            client.chat.completions.create(
                model=config.big_model, messages=[{"role": "system", "content": prompt}]
            )
            .choices[0]
            .message.content
        )

    response = final_response
    output["models"]["large"]["tokens"] = token_count(
        config.big_model, prompt
    ) + token_count(config.big_model, response)
    output["runtime"] = time.time() - start_time
    output["output"]["sources"] = source_ids
    output["output"]["answer"] = response

    if print_mode:
        print("\n\n")
        print(
            colors.green(f"SM Small Model:  ") + str(output["models"]["small"]["name"])
        )
        print(
            colors.green(f"SM Total Tokens: ")
            + str(output["models"]["small"]["tokens"])
        )
        print()
        print(
            colors.green(f"LM Large Model:  ") + str(output["models"]["large"]["name"])
        )
        print(
            colors.green(f"LM Total Tokens: ")
            + str(output["models"]["large"]["tokens"])
        )
        print()
        print(
            colors.green(f"Total Tokens:    ")
            + str(
                output["models"]["small"]["tokens"]
                + output["models"]["large"]["tokens"]
            )
        )
        print(
            colors.green(f"Total Runtime:   ")
            + f'{round(output["runtime"], 2)} seconds ({round(output["runtime"] / 60, 2)} minutes)'
        )

    return output
