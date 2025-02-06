from bs4 import BeautifulSoup
import requests
import json
import os


def get_together_models():
    try:
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
    except:
        return None


def get_deepseek_models():
    try:
        url = "https://api.deepseek.com/models"
        api_key = os.environ.get("DEEP_SEEK_API_KEY")
        if not api_key:
            raise Exception("DEEP_SEEK_API_KEY not set in environment")
        headers = {"Accept": "application/json", "Authorization": f"Bearer {api_key}"}
        resp = requests.get(url, headers=headers)
        json_resp = resp.json()
        model_ids = [
            item.get("id") for item in json_resp.get("data", []) if item.get("id")
        ]
        return sorted(set(model_ids))
    except:
        return None


def get_perplexity_models():
    try:
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
    except:
        return None


def get_groq_models():
    try:
        url = "https://api.groq.com/openai/v1/models"
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise Exception("GROQ_API_KEY not set in environment")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.get(url, headers=headers)
        json_resp = resp.json()
        data = json_resp.get("data", [])
        model_ids = [item.get("id") for item in data if item.get("id")]
        return sorted(set(model_ids))
    except:
        return None


if __name__ == "__main__":
    # NOTE: this was last updated on 2-6-2025
    platforms = {
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "env_name": "GROQ_API_KEY",
            "docs": "https://console.groq.com/docs/overview",
            "models": get_groq_models(),
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com",
            "env_name": "DEEP_SEEK_API_KEY",
            "docs": "https://api-docs.deepseek.com/",
            "models": get_deepseek_models(),
        },
        "together_ai": {
            "base_url": "https://api.together.xyz/v1",
            "env_name": "TOGETHER_API_KEY",
            "docs": "https://docs.together.ai/docs/introduction",
            "models": get_together_models(),
        },
        "perplexity_ai": {
            "base_url": "https://api.perplexity.ai",
            "env_name": "PERPLEXITY_AI_API_KEY",
            "docs": "https://docs.perplexity.ai/home",
            "models": get_perplexity_models(),
        },
    }

    print(json.dumps(platforms, indent=4))
