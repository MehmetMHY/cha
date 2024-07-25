import requests
import json
import re
import html
import copy

from cha import scrapper, colors


def get_item(item_id, errors):
    url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        errors.append(f"HTTP error occurred while fetching item {item_id}: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        errors.append(
            f"Connection error occurred while fetching item {item_id}: {conn_err}"
        )
    except requests.exceptions.Timeout as timeout_err:
        errors.append(f"Timeout occurred while fetching item {item_id}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        errors.append(f"An error occurred while fetching item {item_id}: {req_err}")
    return None


def decode_html(item):
    if "text" in item:
        item["text"] = html.unescape(item["text"])
    if "comments" in item:
        for comment in item["comments"]:
            decode_html(comment)


def get_comments(item, errors):
    comments = []
    if "kids" in item:
        for kid_id in item["kids"]:
            comment = get_item(kid_id, errors)
            if comment:
                comment["comments"] = get_comments(
                    comment, errors
                )  # Recursive call for sub-comments
                comments.append(comment)
    return comments


def get_post_and_comments(post_id, errors):
    post = get_item(post_id, errors)
    if post:
        post["comments"] = get_comments(post, errors)
        decode_html(post)
        return post
    return None


def extract_post_id(url):
    match = re.match(r"^https:\/\/news\.ycombinator\.com\/item\?id=(\d+)$", url)
    if match:
        return int(match.group(1))
    else:
        return None


def fetch_hacker_news_post(url):
    errors = []
    post_id = extract_post_id(url)

    if post_id is None:
        errors.append("Invalid Hacker News post URL. Please enter a valid URL.")
        return {"errors": errors}

    post_data = get_post_and_comments(post_id, errors)

    if post_data is None:
        return {"errors": errors}

    scrapped_content = None
    try:
        url_in_post = str(post_data["url"]).replace(" ", "")

        # NOTE: last updated on July 24, 2024
        start_targets = [
            "https://news.ycombinator.com/",
            "http://news.ycombinator.com/",
        ]

        page_scrape_continue = True
        for st in start_targets:
            if url_in_post.startswith(st):
                page_scrape_continue = False
                break
        if page_scrape_continue:
            scrapped_content = scrapper.remove_html(scrapper.scrape_html(url_in_post))
    except Exception as err:
        print(err)
        pass

    comments_copy = copy.deepcopy(post_data["comments"])
    del post_data["comments"]
    post_data["url_content"] = scrapped_content
    post_data["errors"] = errors
    post_data["comments"] = comments_copy
    return post_data


def valid_hacker_news_url(url):
    valid_url = extract_post_id(url)
    if valid_url == None:
        return False
    return True


def get_hn_post(url):
    final_output = None
    try:
        print(colors.yellow(f"\nScrapping Hacker News Post {url}\n"))
        output = fetch_hacker_news_post(url)
        all_keys = len(list(output.keys()))
        if len(list(output.keys())) == 1 and all_keys == ["errors"]:
            final_output = None
        else:
            # NOTE: the result is converted to a str for the model to easily process
            final_output = json.dumps(output)
    except:
        final_output = None

    if final_output == None:
        print(colors.red("Failed to scrape HN post {url}\n"))

    return final_output
