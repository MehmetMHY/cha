import requests
import openai
import json
import ast
import time
import os

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def brave_search(search_input):
    # (March 9, 2024) Setup Brave API key here:
    #       https://api.search.brave.com/app/dashboard
    
    params = {
        # required: The user's search query term
        "q": search_input,

        # optional: The search query country
        "country": "us",

        # optional: The search language preference
        "search_lang": "en",

        # optional: User interface language preferred in response
        "ui_lang": "en-US",

        # optional: The number of search results returned in response
        "count": 5,

        # optional: The zero-based offset for pagination
        "offset": 0,

        # optional: Filters search results for adult content
        "safesearch": "moderate",

        # optional: Filters search results by when they were discovered
        "freshness": "none",

        # optional: Specifies if text decorations should be applied
        "text_decorations": 1,

        # optional: Specifies if spellcheck should be applied
        "spellcheck": 1,

        # optional: A comma-delimited string of result types to include
        "result_filter": "web,news",
    }

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": os.environ.get("BRAVE_API_KEY"),
    }

    response = requests.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params)

    return response.json()

def generate_search_results(question, model, time_delay=1.5):
    prompt = f"Response to the following question as a JSON (array of strings). Question: Given a complex prompt, decompose it into multiple simpler search engine queries. Complex Prompt: {question}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ]
    )

    queries = ast.literal_eval(response.choices[0].message.content)
    queries.append(prompt)

    results = {}
    for query in list(set(queries)):
        time.sleep(time_delay)

        search = brave_search(query)

        results[query] = {
            "query": search["query"]["original"],
            "pages": []
        }

        for page in search["web"]["results"]:
            results[query]["pages"].append({
                "title": page["title"],
                "url": page["url"],
                "age": page.get("page_age")
            })

    return results

def get_sources(query):
    try:
        response = generate_search_results(
            query,
            "gpt-3.5-turbo-1106",
            1.5
        )
        return response
    except:
        return None
