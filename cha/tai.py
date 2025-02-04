from together import Together
import requests
import json
import sys
import os


def together_models():
    url = "https://api.together.xyz/v1/models"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {os.environ.get('TOGETHER_API_KEY')}",
    }

    response = requests.get(url, headers=headers)

    output = {}
    for entry in json.loads(response.text):
        output[entry["id"]] = entry

    return output


client = Together()

prompt = input("PROMPT: ")

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[
        {"role": "user", "content": prompt},
    ],
    max_tokens=12792,
    temperature=0.7,
    top_p=0.7,
    top_k=50,
    repetition_penalty=1,
    stream=True,
)

for chunk in response:
    if chunk.choices and len(chunk.choices) > 0:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
