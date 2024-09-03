from bs4 import BeautifulSoup
import requests
import json

import colors


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


def test_scrapper_get_models():
    try:
        model_list = get_models()
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
