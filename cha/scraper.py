import concurrent.futures
import signal
import string
import time
import json
import re
import os
import uuid

# 3rd party packages
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from cha import youtube, colors


def extract_urls(text):
    url_pattern = r"https?://(?:www\.)?\S+"
    urls = re.findall(url_pattern, text)
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


def process_url(url):
    try:
        if youtube.valid_yt_link(url):
            content = youtube.main_yt_pointer(url)
        elif valid_pdf_url(url):
            content = scrape_pdf_url(url)
        else:
            content = main_general_scraper(url)
    except:
        content = None
    return url, content


def get_all_htmls(text):
    urls = list(set(extract_urls(text)))
    if not urls:
        return {}

    output = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(process_url, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url, content = future.result()
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


def valid_pdf_url(url):
    if url.startswith("https://arxiv.org/pdf/"):
        return True
    if url.startswith("http://arxiv.org/pdf/"):
        return True
    if url.endswith(".pdf"):
        return True
    return False


def scrape_pdf_url(url):
    try:
        response = requests.get(url)
        if response.headers.get("Content-Type") == "application/pdf":
            filename = f"cha_{uuid.uuid4()}.pdf"
            with open(filename, "wb") as file:
                file.write(response.content)

            # extract text from the PDF
            document = fitz.open(filename)
            text = ""
            for page_num in range(len(document)):
                page = document.load_page(page_num)
                text += page.get_text()

            # delete the PDF file
            os.remove(filename)

            return text

        raise Exception(f"URL {url} is NOT a valid PDF file")
    except requests.RequestException as e:
        print(colors.red(f"Failed to load PDF URL {url} due to {e}"))
