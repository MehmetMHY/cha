import requests
import os
import fitz  # PyMuPDF
import uuid

from cha import colors


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
