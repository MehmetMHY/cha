from bs4 import BeautifulSoup
import requests
import json


# NOTE (6-30-2024): Anthropic's API lacks an endpoint for fetching the latest supported models, so web scraping is required
def get_models():
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
