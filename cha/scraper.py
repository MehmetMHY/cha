import signal
import string
import time
import json
import requests
import re

# 3rd party packages
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from bs4 import BeautifulSoup
from cha import youtube, pdfs, colors


def extract_urls(text):
    urls = []
    for word in text.split(" "):
        if len(word) <= 6:
            continue
        if "http" in word.lower() and "//" in word.lower():
            urls.append(word)
    return urls


def remove_html(content):
    oline = content
    soup = BeautifulSoup(oline, "html.parser")
    for data in soup(["style", "script"]):
        data.decompose()
    tmp = " ".join(soup.stripped_strings)
    tmp = "".join(filter(lambda x: x in set(string.printable), tmp))
    tmp = re.sub(" +", " ", tmp)
    return tmp


class TimeoutException(Exception):
    pass


def timeout(seconds=10, error_message="function call timed out"):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutException(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)  # disable the alarm
            return result

        return wrapper

    return decorator


@timeout(seconds=60)
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


def fast_scraper(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"An error occurred: {e}"


def main_general_scraper(url):
    user_input = input(colors.yellow("Use Advance Web Scraper (y/n)? "))
    print()

    use_advance = False
    if user_input.lower() in ["y", "yes"]:
        use_advance = True

    content = ""
    if use_advance:
        # NOTE: this uses Selenium for scraping which should work on almost all websites but it's very slow
        content = scrape_html(url)
    else:
        # NOTE: this just uses HTTP which is faster but not all websites allow this
        content = fast_scraper(url)

    return remove_html(content)


def get_all_htmls(text):
    urls = list(set(extract_urls(text)))
    if len(urls) == 0:
        return {}

    output = {}
    for url in urls:
        content = None
        try:
            if youtube.valid_yt_link(url):
                content = youtube.main_yt_pointer(url)
            elif pdfs.valid_pdf_url(url):
                content = pdfs.scrape_pdf_url(url)
            else:
                content = main_general_scraper(url)
        except:
            content = None
        output[url] = content

    return output


def scraped_prompt(prompt):
    htmls = get_all_htmls(prompt)
    if htmls == {}:
        return prompt

    new_prompt = """
Here is the content from the following url(s) in the form of a JSON:
```
{0}
```

Knowing this, can you answer the following prompt: {1}
""".format(
        json.dumps(htmls), prompt
    )

    return new_prompt


# NOTE (6-30-2024): Anthropic's API lacks an endpoint for fetching the latest supported models, so web scraping is required
def get_anthropic_models():
    url = "https://docs.anthropic.com/en/docs/about-claude/models"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    data_dict = []
    tables = soup.find_all("table")
    for table in tables:
        headers = [header.get_text().strip() for header in table.find_all("th")]
        rows = table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            if cells:
                row_data = [cell.get_text().strip() for cell in cells]
                data_dict.append(dict(zip(headers, row_data)))

    data_dict = data_dict[:6]

    for d in data_dict:
        keys_to_remove = [
            key
            for key, value in d.items()
            if "coming soon" in value.lower() or "later this year" in value.lower()
        ]
        for key in keys_to_remove:
            del d[key]
    data_dict = [d for d in data_dict[:6] if not (len(d) == 1 and "Model" in d)]

    output = []
    for entry in data_dict:
        model = entry.get("Model")
        model_id = entry.get("Anthropic API")
        if model and model_id:
            output.append({"name": model, "model": model_id})

    return output


def test_scraper_get_anthropic_models():
    try:
        model_list = get_anthropic_models()
    except Exception as e:
        print(colors.red(f"Error: Failed to get models - {str(e)}"))
        return False

    if model_list is None:
        print(colors.red("Error: Model list is None"))
        return False

    if not isinstance(model_list, list):
        print(colors.red(f"Error: Model list is not a list, got {type(model_list)}"))
        return False

    all_tests_passed = True

    for i, item in enumerate(model_list):
        if not isinstance(item, dict):
            print(colors.red(f"Error: Item {i} is not a dictionary, got {type(item)}"))
            all_tests_passed = False
            continue

        if "name" not in item:
            print(colors.red(f"Error: Item {i} is missing 'name' key"))
            all_tests_passed = False
        elif not isinstance(item["name"], str):
            print(
                colors.red(
                    f"Error: Item {i} 'name' is not a string, got {type(item['name'])}"
                )
            )
            all_tests_passed = False
        elif len(item["name"]) == 0:
            print(colors.red(f"Error: Item {i} 'name' is an empty string"))
            all_tests_passed = False

        if "model" not in item:
            print(colors.red(f"Error: Item {i} is missing 'model' key"))
            all_tests_passed = False
        elif not isinstance(item["model"], str):
            print(
                colors.red(
                    f"Error: Item {i} 'model' is not a string, got {type(item['model'])}"
                )
            )
            all_tests_passed = False
        elif len(item["model"]) == 0:
            print(colors.red(f"Error: Item {i} 'model' is an empty string"))
            all_tests_passed = False

    return all_tests_passed
