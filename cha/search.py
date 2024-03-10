import concurrent.futures
import requests
import openai
import json
import ast
import time
import os
import sys
import re

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import tiktoken

from cha import scrapper

# hard coded config variables
main_embedding_model ="cl100k_base"
cheap_model = "gpt-3.5-turbo-1106"
cheap_model_max_token = ( 16385 ) - 100
big_model = "gpt-4-turbo-preview"

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def brave_search(search_input):
    # (March 9, 2024) Setup Brave API key here:
    #       https://api.search.brave.com/app/dashboard
    
    params = {
        # required: The user's search query term
        "q": search_input,

        # optional: The search query country
        "country": "us",

        # optional: The search language preference
        "search_lang": "en",

        # optional: User interface language preferred in response
        "ui_lang": "en-US",

        # optional: The number of search results returned in response
        "count": 5,

        # optional: The zero-based offset for pagination
        "offset": 0,

        # optional: Filters search results for adult content
        "safesearch": "moderate",

        # optional: Filters search results by when they were discovered
        "freshness": "none",

        # optional: Specifies if text decorations should be applied
        "text_decorations": 1,

        # optional: Specifies if spellcheck should be applied
        "spellcheck": 1,

        # optional: A comma-delimited string of result types to include
        "result_filter": "web,news",
    }

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": os.environ.get("BRAVE_API_KEY"),
    }

    response = requests.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)

    return response.json()

def generate_search_results(question, model, time_delay=1.5):
    prompt = f"Response to the following question as a JSON (array of strings). Question: Given a complex prompt, decompose it into multiple simpler search engine queries. Complex Prompt: {question}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )

    queries = ast.literal_eval(response.choices[0].message.content)
    queries.append(prompt)

    results = {}
    for query in list(set(queries)):
        try:
            time.sleep(time_delay)

            search = brave_search(query)

            results[query] = {
                "query": search["query"]["original"],
                "pages": []
            }

            for page in search["web"]["results"]:
                results[query]["pages"].append({
                    "title": page["title"],
                    "url": page["url"],
                    "age": page.get("page_age")
                })
        except:
            pass

    return results

def get_sources(query):
    try:
        response = generate_search_results(
            query,
            cheap_model,
            2.0
        )
        return response
    except Exception as err:
        print(err)
        return None

def token_count(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def adjust_prompt_to_token_limit(model, prompt: str, token_limit: int) -> str:
    num_tokens = token_count(prompt, model)
    while num_tokens > token_limit and token_limit >= 0:
        diff = int( (num_tokens - cheap_model_max_token) / 2 )
        if diff == 0:
            diff = 1
        prompt = prompt[:-(diff)]
        num_tokens = token_count(prompt, model)
    return prompt
    
def convert_search_results(search_results):
    for key in search_results:
        pages_list = search_results[key]["pages"]
        url_dict = {}
        for page in pages_list:
            url = page.get("url")
            if url:
                page_info = {k: v for k, v in page.items() }
                url_dict[url] = page_info
                url_dict[url]["content"] = ""
        search_results[key]["pages"] = url_dict
    return search_results

def is_valid_url(url):
    # LAST UPDATED: March 10, 2024

    # Expanded list of file extensions to exclude
    excluded_extensions = [
        '.pdf', '.xml', '.css', '.docx', '.xlsx', '.pptx', '.zip', '.rar',
        '.exe', '.dmg', '.tar.gz', '.mp3', '.mp4', '.avi', '.mov', '.jpg',
        '.jpeg', '.png', '.gif', '.bmp', '.csv', '.json', '.txt', '.ppt',
        '.pptx', '.doc', '.xls', '.rtf', '.7z', '.iso', '.wav', '.mkv'
    ]

    # Optional: Make a HEAD request to check the Content-Type (not included in this snippet)
    # You would need to use requests.head(url).headers['Content-Type'] and check if it starts with 'text/html'

    # Check if the URL ends with any of the excluded extensions
    if any(url.lower().endswith(ext) for ext in excluded_extensions):
        return False

    # Additional patterns to exclude URLs that are likely non-HTML content
    # These patterns match common file naming conventions on the web
    patterns = [
        r"/[^/?#]+\.[^/?#]+($|\?|#)",  # Paths with a file extension
        r"/[^/?#]+/download($|\?|#)",  # URLs with "download" in the last path segment
        r"/api/",                      # URLs that likely point to an API endpoint
        r"/[^/?#]+\.php($|\?|#)"       # PHP files (often dynamic but can be used for downloads)
    ]

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
        options.add_argument('--headless')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)

        # wait for page to load
        time.sleep(time_delay)

        return driver.page_source
    finally:
        driver.quit()

def scrape_urls_in_parallel(urls, max_workers=20):
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(scrape_html, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                html_content = future.result()
                results[url] = html_content
            except Exception as exc:
                print(f"Error for {url}: {exc}")
                results[url] = None
    return results

def summarize_urls_data(scrapped_url_data):
    sum_scrapped_url_data = {}

    for key in scrapped_url_data:
        response = None
        try:
            prompt = f"Summarize the following text into one paragraph:\n```\n{scrapped_url_data[key]}\n```"
            prompt = adjust_prompt_to_token_limit(main_embedding_model, prompt, cheap_model_max_token)
            response = client.chat.completions.create(
                model=cheap_model,
                messages=[{ "role": "system", "content": prompt }]
            ).choices[0].message.content
        except:
            pass

        sum_scrapped_url_data[key] = response

    return sum_scrapped_url_data

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
    prompt = prompt.rstrip('\n') + "\n```\n\n"
    prompt += f"Answer the following question (make sure to site the sources by JUST using their respected number/id):\n```\n{question}\n```"
    
    return {
        "prompt": prompt,
        "ids": source_ids
    }

# main function
def answer_search(user_question):
    start_time = time.time()

    # gather search browser results/data
    search_results = get_sources(user_question)
    search_results = convert_search_results(search_results)

    # scrape all webpages rathered from the browser
    all_urls = convert_all_urls(search_results)
    scrapped_url_data = scrape_urls_in_parallel(all_urls, len(all_urls))
    for url in scrapped_url_data:
        scrapped_url_data[url] = scrapper.remove_html(scrapped_url_data[url])

    # reduce token count by summarizing a lot of the results
    scrapped_url_data = summarize_urls_data(scrapped_url_data)

    # create main prompt for big model
    prompt_data = research_prompt(scrapped_url_data, user_question)
    prompt = prompt_data["prompt"]
    source_ids = prompt_data["ids"]

    # send final prompt to the big model
    response = client.chat.completions.create(
        model=big_model,
        messages=[{ "role": "system", "content": prompt }]
    ).choices[0].message.content

    runtime = time.time() - start_time

    return {
        "runtime": runtime,
        "answer": response,
        "sources": source_ids
    }
