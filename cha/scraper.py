import concurrent.futures
import string
import json
import re
import os
import uuid

import requests
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
from cha import youtube, colors, utils


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


def basic_scraper(url):
    try:
        response = utils.get_request(url)
        if response == None:
            raise Exception(f"http GET request failed due to an error code or timeout")
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"


def process_url(url):
    try:
        if youtube.valid_yt_link(url):
            content = youtube.youtube_scraper(url)
        elif valid_pdf_url(url):
            content = scrape_pdf_url(url)
        else:
            content = remove_html(basic_scraper(url))
    except:
        content = None
    return url, content


def get_all_htmls(text):
    urls = None
    if type(text) == str:
        urls = list(set(extract_urls(text)))
        if not urls:
            return {}
    elif type(text) == list:
        urls = text
    else:
        raise Exception(f"{get_all_htmls.__name__}() only excepts type list or str")

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
        response = utils.get_request(url)
        if response == None:
            raise Exception(f"http GET request failed due to an error code or timeout")

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
    except Exception as e:
        print(colors.red(f"Failed to load PDF URL {url} due to {e}"))
