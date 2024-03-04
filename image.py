"""
March 4, 2024

This code is in beta, it's not recommended for us right now
"""

# https://platform.openai.com/docs/api-reference/images

import requests
from openai import OpenAI
import sys
import json
import datetime
import time

client = OpenAI()

def img_filename(model, s, max_word=10):
    filtered_chars = ''.join(filter(lambda c: c.isalpha() or c.isspace(), s))
    filtered_chars = filtered_chars.lower()
    content = [
        model.lower(),
        "__",
        str(int(time.time())),
        "__",
        "_".join(filtered_chars.split(" ")[:max_word]),
        ".jpg"
    ]
    return "".join(content)

def simple_date(epoch_time):
    date_time = datetime.datetime.fromtimestamp(epoch_time)
    formatted_date = date_time.strftime("%B %d, %Y")
    return formatted_date

def pick_img_model():
    response = client.models.list()
    if not response.data:
        raise ValueError('No models available')

    openai_models = [
        (model.id, model.created) 
        for model in response.data 
        if "dall" in model.id
    ]

    max_length = max(len(model_id) for model_id, _ in openai_models)
    openai_models = sorted(openai_models, key=lambda x: x[1])
    models = []
    print("Available OpenAI Models:")
    for model_id, created in openai_models:
        models.append(model_id)
        formatted_model_id = model_id.ljust(max_length)
        print(f"   > {formatted_model_id}   {simple_date(created)}")
    picked_model = input("Model: ")

    if picked_model not in models:
        raise Exception(f"Model {picked_model} is NOT a supported model by OpenAI")
    return picked_model

def save_url_img(filepath, url):
    try:
        image_data = requests.get(url).content
        with open(filepath, 'wb') as handler:
            handler.write(image_data)
    except Exception as err:
        print(f"Failed to grab image: {err}")
    return

def get_quality():
    choice = input("Quality: ")
    choice = choice.lower().replace(" ", "")
    if choice != "standard" and choice != "hd":
        raise Exception(f"{choice} is not a supported quality")
    return choice

def get_n():
    try:
        choice = input("N: ")
        choice = int(choice.replace(" ", ""))
        if choice < 1:
            raise Exception(f"n has to be 1 or greater")
        return choice
    except:
        raise Exception(f"n can only be an int")

def get_size():
    try:
        width = int(input("Width: "))
        height = int(input("Height: "))
        return f"{width}x{height}"
    except:
        raise Exception(f"width and height can only be int(s)")

# MAIN FUNCTION CALLS

model = pick_img_model()
prompt = input("Prompt: ")
quality = get_quality()
n = get_n()
size = get_size()

response = client.images.generate(
  model=model,
  prompt=prompt,
  size=size,
  quality=quality,
  n=n,
)

for i in range(len(response.data)):
    url = response.data[i].url
    filename = img_filename(model, prompt)
    save_url_img(filename, url)
    print(f"Created Image: {filename}")

