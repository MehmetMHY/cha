import signal
import string
import time
import json
import re

# 3rd party packages
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from bs4 import BeautifulSoup
from cha import youtube, pdfs


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
                content = remove_html(scrape_html(url))
        except:
            content = None
        output[url] = content

    return output


def scrapped_prompt(prompt):
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
