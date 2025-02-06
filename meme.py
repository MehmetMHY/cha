"""
# get all supported Together.AI models

curl -s --request GET --url https://api.together.xyz/v1/models --header 'accept: application/json' --header "authorization: Bearer $TOGETHER_API_KEY" | jq '.[] | select(.type == "chat") | .id' | tr -d '"' | sort | uniq

# get all supported DeepSeek models by DeepSeek directory

curl -s --request GET --url https://api.deepseek.com/models --header 'Accept: application/json' --header "Authorization: Bearer $DEEP_SEEK_API_KEY" | jq -r '.data[].id' | sort | uniq

# get all supported Perplexity models

curl -s https://docs.perplexity.ai/guides/model-cards | tr "{\|}" "\n" | grep "              children: " | awk '{print $3}' | tr -d '\\\|"n' | sort -r | uniq

# get all supported Groq models

curl -s -X GET "https://api.groq.com/openai/v1/models" -H "Authorization: Bearer $GROQ_API_KEY" -H "Content-Type: application/json" | jq -r '.data[].id' | sort | uniq
"""

from bs4 import BeautifulSoup
import requests
import copy
import json
import os


def get_together_models():
    """
    Retrieve all Together.AI chat models.
    Filters models whose "type" is "chat" and returns a sorted list of unique IDs.
    """
    url = "https://api.together.xyz/v1/models"
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        raise Exception("TOGETHER_API_KEY not set in environment")
    headers = {"accept": "application/json", "authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    # data is assumed to be a list of model dicts. Filter chat models.
    model_ids = [
        model.get("id")
        for model in data
        if model.get("type") == "chat" and model.get("id")
    ]
    # Remove duplicates and sort
    return sorted(set(model_ids))


def get_deepseek_models():
    """
    Retrieve all DeepSeek models.
    Returns a sorted list of unique model IDs from the 'data' field.
    """
    url = "https://api.deepseek.com/models"
    api_key = os.environ.get("DEEP_SEEK_API_KEY")
    if not api_key:
        raise Exception("DEEP_SEEK_API_KEY not set in environment")
    headers = {"Accept": "application/json", "Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers)
    json_resp = resp.json()
    # Assuming the models are in json_resp['data'] list.
    model_ids = [item.get("id") for item in json_resp.get("data", []) if item.get("id")]
    return sorted(set(model_ids))


def get_perplexity_models():
    """
    Retrieves the supported models from Perplexity by making a GET request
    to the model-cards URL and parsing the returned HTML.
    It extracts all <code> elements from table rows and returns a sorted
    list of unique model names.
    """
    url = "https://docs.perplexity.ai/guides/model-cards"
    response = requests.get(url)

    soup = BeautifulSoup(response.content, "html.parser")
    models = set()

    # Look for all <table> tags (both supported and legacy models)
    tables = soup.find_all("table")
    for table in tables:
        # Each table row is a <tr>; skip header rows.
        for row in table.find_all("tr"):
            code_tag = row.find("code")
            if code_tag:
                model = code_tag.get_text(strip=True)
                models.add(model)

    # Return the models sorted in reverse alphabetical order (to mimic bash sort -r)
    return sorted(models, reverse=True)


def get_groq_models():
    """
    Retrieve all Groq models.
    Returns a sorted list of unique model IDs from JSON response 'data' list.
    """
    url = "https://api.groq.com/openai/v1/models"
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise Exception("GROQ_API_KEY not set in environment")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.get(url, headers=headers)
    json_resp = resp.json()
    data = json_resp.get("data", [])
    model_ids = [item.get("id") for item in data if item.get("id")]
    return sorted(set(model_ids))


def user_select_platform(platforms):
    platform_names = list(platforms.keys())

    print("Available platforms:")
    for i, platform in enumerate(platform_names, 1):
        print(f"{i}. {platform}")

    while True:
        try:
            platform_choice = (
                int(input("Enter the number for your platform choice: ")) - 1
            )
            chosen_platform = platform_names[platform_choice]
            break
        except (IndexError, ValueError):
            print("Invalid choice, please select a number from the list.")

    models = platforms[chosen_platform]["models"]

    print("Available models:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model}")

    while True:
        try:
            model_choice = int(input("Enter the number for your model choice: ")) - 1
            chosen_model = models[model_choice]
            break
        except (IndexError, ValueError):
            print("Invalid choice, please select a number from the list.")

    sdk_config = copy.deepcopy(platforms[chosen_platform])
    sdk_config["picked_model"] = chosen_model
    return sdk_config


if __name__ == "__main__":
    platforms = {
        "groq": {
            "models": get_groq_models(),
            "base_url": "https://api.groq.com/openai/v1",
            "env_name": "GROQ_API_KEY",
            "docs": "https://console.groq.com/docs/overview",
        },
        "deepseek": {
            "models": get_deepseek_models(),
            "base_url": "https://api.deepseek.com",
            "env_name": "DEEP_SEEK_API_KEY",
            "docs": "https://api-docs.deepseek.com/",
        },
        "together_ai": {
            "models": get_together_models(),
            "base_url": "https://api.together.xyz/v1",
            "env_name": "TOGETHER_API_KEY",
            "docs": "https://docs.together.ai/docs/introduction",
        },
        "perplexity_ai": {
            "models": get_perplexity_models(),
            "base_url": "https://api.perplexity.ai",
            "env_name": "PERPLEXITY_AI_API_KEY",
            "docs": "https://docs.perplexity.ai/home",
        },
    }

    output = user_select_platform(platforms)
    print(json.dumps(output, indent=4))
