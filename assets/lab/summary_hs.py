from openai import OpenAI
import statistics
import tiktoken
import time
import math
import json
import sys
import os
import re
import concurrent.futures
import random


REPLACEMENT_SUBSTRING_TARGETS = {
    "<think>": "",
    "\\": "",
    "```": "",
    "\n": " ",
    "<": "",
    ">": "",
    "{": "",
    "}": "",
    "|": "",
    "[": "",
    "]": "",
    "(": "",
    ")": "",
    ",": "",
    "!": "",
    "?": "",
    "...": "",
    ":": "",
    ";": "",
    ".": "",
    "^": "",
    "#": "",
    "`": "",
    "-": "",
    '"': "",
    "“": "",
    "”": "",
    "_": "",
    "'": "",
    "‘": "",
    "’": "",
    "$": "",
    "€": "",
    "£": "",
    "¥": "",
    "₹": "",
    "₩": "",
    "=": "",
    "+": "",
    "–": "",
    "—": "",
    "PROMPT": "",
    "HTTP": "",
    "INFO": "",
    "ERROR": "",
    "WARNING": "",
    "DEBUG": "",
    "TRACE": "",
    "FATAL": "",
    "CRITICAL": "",
    "REDACTED": "",
    "//": "",
    "/": "",
    "*": "",
    "~": "",
}


def count_tokens(
    text, model_name="gpt-4o", fast_mode=False, language=None, rounding=1.25
):
    try:
        if fast_mode == False:
            try:
                encoding = tiktoken.encoding_for_model(model_name)
                return len(encoding.encode(text))
            except:
                new_model_name = "o1" if model_name.startswith("o") else "gpt-4o"
                encoding = tiktoken.encoding_for_model(new_model_name)
                return len(encoding.encode(text))

        word_count = len(text.split())

        # https://gptforwork.com/guides/openai-gpt3-tokens
        token_multiplier = {
            "english": 1.3,
            "french": 2.0,
            "german": 2.1,
            "spanish": 2.1,
            "chinese": 2.5,
            "russian": 3.3,
            "vietnamese": 3.3,
            "arabic": 4.0,
            "hindi": 6.4,
        }

        if language is None or str(language.lower()) not in token_multiplier:
            tokens = word_count * statistics.median(token_multiplier.values())
        else:
            tokens = word_count * token_multiplier[language.lower()]

        return math.floor(tokens * rounding)
    except Exception as e:
        print(e)
        return None


def load_all_json_from_history(history_dir):
    json_data = []
    if os.path.exists(history_dir) and os.path.isdir(history_dir):
        for filename in os.listdir(history_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(history_dir, filename)
                with open(file_path, "r") as f:
                    data = json.load(f)
                    json_data.append(
                        {"filename": filename, "filepath": file_path, "data": data}
                    )
    return json_data


def save_trimmed_text(original_filepath, trimmed_text, token_count):
    base_name = os.path.splitext(original_filepath)[0]
    trimmed_filepath = f"{base_name}_trimmed.txt"

    with open(trimmed_filepath, "w") as f:
        f.write(f"Original file: {os.path.basename(original_filepath)}\n")
        f.write(f"Token count: {token_count}\n")
        f.write(f"Content:\n{trimmed_text}")

    return trimmed_filepath


def remove_emails(text):
    return " ".join([word for word in text.split() if "@" not in word])


def remove_urls(text):
    url_pattern = r"https?://\S+|www\.\S+"
    return re.sub(url_pattern, "", text)


def remove_filenames(text):
    filename_pattern = r"\b\w+(?:_\d+)?\.\w{2,6}\b"
    return re.sub(filename_pattern, "", text)


def multi_replace(text, replacements):
    pattern = re.compile("|".join(map(re.escape, replacements.keys())))
    return pattern.sub(lambda m: replacements[m.group(0)], text)


def remove_multiple_spaces(text):
    return re.sub(r"\s+", " ", text).strip()


def remove_filepaths(text):
    pattern = (
        r'([a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*|'
        r"/(?:[^/\s]+/)*[^/\s]+)"
    )
    return re.sub(pattern, "", text)


def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
        "\U00002700-\U000027bf"  # Dingbats
        "\U00002600-\U000026ff"  # Miscellaneous Symbols
        "\u200d"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


def remove_hex_colors(text):
    pattern = r"\b0x[0-9a-fA-F]{6}\b"
    return re.sub(pattern, "", text)


def remove_hex_hashes(text):
    pattern = r"\b[a-fA-F0-9]{32}\b"
    return re.sub(pattern, "", text)


def remove_long_numbers(text):
    pattern = r"\b\d{5,}\b"
    return re.sub(pattern, "", text)


def process_history_text(history_item, max_token_limit, model_name):
    filename = history_item["filename"]
    chat_json = history_item["data"]["chat"]

    text = ""
    first_entry = True
    for entry in chat_json:
        if first_entry:
            first_entry = False
            continue
        user = entry["user"]
        text = text + " " + user

    text = remove_emails(text)
    text = remove_urls(text)
    text = remove_filenames(text)
    text = remove_filepaths(text)
    text = remove_emojis(text)
    text = remove_hex_colors(text)
    text = remove_hex_hashes(text)
    text = remove_long_numbers(text)
    text = multi_replace(text, REPLACEMENT_SUBSTRING_TARGETS)
    text = remove_multiple_spaces(text)

    return filename, text


def llm_summarize_prompt(target):
    prompt = f"""
Summarize the following random text in a single, short sentence. Be concise. 
Only output the summary, with no extra explanation or formatting.

Text:
{target}

IMPORTANT: Do not explain, do not narrate, do not say anything except the summary sentence!
""".strip()
    return prompt


def llm_full_summarize_prompt(full_history):
    prompt = f"""
Summarize the following chat history into a 3-4 sentence summary if the history is very long. If the history is short, just summarize it in a 1-5 sentences. Focus on the topics discussed, problems solved, and concepts explored rather than who did what. Write the summary professionally and describe the content neutrally.

Chat history:
{full_history}

IMPORTANT: Do not explain, do not narrate, do not say anything except the summary sentence! Also DO NOT include citations or references, just the summary. Do not mention "user" or "assistant" - just describe the topics and content discussed.
""".strip()
    return prompt


def process_single_item(item, max_token_limit, model_name, client):
    filename, text = process_history_text(item, max_token_limit, model_name)
    prompt = llm_summarize_prompt(text)

    short_summary = (
        client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt.strip()}],
            stream=False,
            max_tokens=50,
            temperature=0.2,
        )
        .choices[0]
        .message.content.strip()
    )

    full_chat_history = str(item["data"]["chat"])
    full_chat_history = full_chat_history.replace("{", "").replace("}", "")
    full_chat_history = re.sub(r"\s+", " ", full_chat_history).strip()
    prompt = llm_full_summarize_prompt(full_chat_history)

    long_summary = (
        client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            temperature=0.2,
        )
        .choices[0]
        .message.content.strip()
    )

    return filename, {
        "short_summary": short_summary,
        "long_summary": long_summary,
    }


if __name__ == "__main__":
    MAX_WORKERS = 5
    PROCESS_LIMIT = 5
    max_token_limit = 1_000_000
    model_name = "gpt-4.1-mini"

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    history_dir = os.path.join(os.path.expanduser("~"), ".cha/history")
    all_history = load_all_json_from_history(history_dir)

    random.shuffle(all_history)

    if PROCESS_LIMIT is not None:
        all_history = all_history[:PROCESS_LIMIT]
        print(f"Limited to processing {len(all_history)} files for testing")

    all_summaries = {}

    print(f"Processing {len(all_history)} files with {MAX_WORKERS} workers...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_item = {
            executor.submit(
                process_single_item, item, max_token_limit, model_name, client
            ): item
            for item in all_history
        }

        for future in concurrent.futures.as_completed(future_to_item):
            try:
                filename, summaries = future.result()
                all_summaries[filename] = summaries
                print(f"Completed: {filename}")
            except Exception as exc:
                item = future_to_item[future]
                print(f"Error processing {item['filename']}: {exc}")
    output_file = "chat_history_summaries.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=4, ensure_ascii=False)

    print(f"\nSummaries saved to {output_file}")
    print(f"Processed {len(all_summaries)} files successfully.")
