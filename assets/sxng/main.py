import requests
import json


def search(base_url, query, time_range=None):
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    params = {"q": query, "format": "json"}
    if time_range:
        params["time_range"] = time_range
    response = requests.get(
        base_url.rstrip("/") + "/search", params=params, headers=headers
    )
    response.raise_for_status()
    return response.json()


def main():
    base_url = (
        input("Enter SearxNG base URL (default http://localhost:8080): ").strip()
        or "http://localhost:8080"
    )
    query = input("Enter search query: ").strip()
    print("Time filter: 1) Past day 2) Past month 3) Past year 4) No filter")
    choice = input("Choice (1-4): ").strip()
    time_map = {"1": "day", "2": "month", "3": "year", "4": None}
    time_range = time_map.get(choice, None)
    max_results = input("Max number of results (leave empty for all): ").strip()
    max_results = int(max_results) if max_results.isdigit() else None
    result = search(base_url, query, time_range)
    total_results = len(result.get("results", []))
    if max_results is not None:
        result["results"] = result.get("results", [])[:max_results]
    print(f"Search Results (Output):")
    print(json.dumps(result, indent=4))
    print(f"Total results: {total_results}")


if __name__ == "__main__":
    main()
