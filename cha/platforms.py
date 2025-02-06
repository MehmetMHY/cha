from bs4 import BeautifulSoup
import requests
import copy
import json
import os

from cha import colors, utils


def get_together_models():
    url = "https://api.together.xyz/v1/models"
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        raise Exception("TOGETHER_API_KEY not set in environment")
    headers = {"accept": "application/json", "authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers)
    data = resp.json()
    model_ids = [
        model.get("id")
        for model in data
        if model.get("type") == "chat" and model.get("id")
    ]
    return sorted(set(model_ids))


def get_deepseek_models():
    url = "https://api.deepseek.com/models"
    api_key = os.environ.get("DEEP_SEEK_API_KEY")
    if not api_key:
        raise Exception("DEEP_SEEK_API_KEY not set in environment")
    headers = {"Accept": "application/json", "Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers)
    json_resp = resp.json()
    model_ids = [item.get("id") for item in json_resp.get("data", []) if item.get("id")]
    return sorted(set(model_ids))


def get_perplexity_models():
    # NOTE: (2-5-2025) Perplexity's API does not have an endpoint for getting all models so web scrapping needs to happen
    url = "https://docs.perplexity.ai/guides/model-cards"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    models = set()
    # look for all <table> tags (both supported and legacy models)
    tables = soup.find_all("table")
    for table in tables:
        # each table row is a <tr>; skip header rows.
        for row in table.find_all("tr"):
            code_tag = row.find("code")
            if code_tag:
                model = code_tag.get_text(strip=True)
                models.add(model)
    # return the models sorted in reverse alphabetical order (to mimic bash sort -r)
    return sorted(models, reverse=True)


def get_groq_models():
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


def user_select_platform(platforms, chosen_platform=None, chosen_model=None):
    if chosen_platform is not None and chosen_model is not None:
        if chosen_platform not in platforms:
            raise Exception(f"Platform {chosen_platform} is not a supported platform")
        try:
            models = platforms[chosen_platform]["models"]()
        except Exception as e:
            raise Exception(f"Error loading models for platform {chosen_platform}: {e}")
        if chosen_model not in models:
            raise Exception(
                f"Model {chosen_model} for platform {chosen_platform} is not a supported model"
            )
        sdk_config = copy.deepcopy(platforms[chosen_platform])
        sdk_config["picked_model"] = chosen_model
        sdk_config["platform"] = chosen_platform
        del sdk_config["models"]
        return sdk_config

    # continue with the slow process with selecting a valid platform and model name

    none_error_platforms = {}
    for platform in platforms:
        try:
            value = copy.deepcopy(platforms[platform])
            value["models"] = platforms[platform]["models"]()
            none_error_platforms[platform] = value
        except Exception:
            pass

    platforms = none_error_platforms
    platform_names = list(platforms.keys())

    if chosen_platform is not None:
        if chosen_platform not in platform_names:
            raise Exception(f"Platform {chosen_platform} is not a supported platform")
    else:
        print(colors.yellow("Available platforms:"))
        for i, platform in enumerate(platform_names, 1):
            print(colors.yellow(f"    {i}) {platform}"))
        while True:
            try:
                platform_choice = (
                    int(utils.safe_input(colors.blue("Select A Platform (Int): "))) - 1
                )
                chosen_platform = platform_names[platform_choice]
                break
            except (IndexError, ValueError):
                print(
                    colors.red("Invalid choice, please select a number from the list.")
                )

    models = platforms[chosen_platform]["models"]

    if chosen_model is not None:
        if chosen_model not in models:
            raise Exception(
                f"Model {chosen_model} for platform {chosen_platform} is not a supported model"
            )
    else:
        print(colors.yellow("Available models:"))
        for i, model in enumerate(models, 1):
            print(colors.yellow(f"    {i}) {model}"))
        while True:
            try:
                model_choice = (
                    int(utils.safe_input(colors.blue("Select A Model (Int): "))) - 1
                )
                chosen_model = models[model_choice]
                break
            except (IndexError, ValueError):
                print(
                    colors.red("Invalid choice, please select a number from the list.")
                )

    sdk_config = copy.deepcopy(platforms[chosen_platform])
    sdk_config["picked_model"] = chosen_model
    sdk_config["platform"] = chosen_platform
    del sdk_config["models"]

    return sdk_config


# main global variable for all the supported external platforms that are not hosted by OpenAI
platforms = {
    "groq": {
        "models": get_groq_models,
        "base_url": "https://api.groq.com/openai/v1",
        "env_name": "GROQ_API_KEY",
        "docs": "https://console.groq.com/docs/overview",
    },
    "deepseek": {
        "models": get_deepseek_models,
        "base_url": "https://api.deepseek.com",
        "env_name": "DEEP_SEEK_API_KEY",
        "docs": "https://api-docs.deepseek.com/",
    },
    "together_ai": {
        "models": get_together_models,
        "base_url": "https://api.together.xyz/v1",
        "env_name": "TOGETHER_API_KEY",
        "docs": "https://docs.together.ai/docs/introduction",
    },
    "perplexity_ai": {
        "models": get_perplexity_models,
        "base_url": "https://api.perplexity.ai",
        "env_name": "PERPLEXITY_AI_API_KEY",
        "docs": "https://docs.perplexity.ai/home",
    },
}
