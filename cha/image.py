import requests
from openai import OpenAI
import sys
import json
import datetime
import time

from cha import colors

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
    return date_time.strftime("%B %d, %Y")

def pick_img_model():
    try:
        response = client.models.list()
        if not response.data:
            print(colors.red('No models available. Exiting...'))
            sys.exit(1)

        openai_models = [(model.id, model.created) for model in response.data if "dall" in model.id]
        openai_models = sorted(openai_models, key=lambda x: x[1], reverse=True)

        print(colors.yellow("Available OpenAI Models:"))
        for model_id, created in openai_models:
            print(colors.yellow(f"   > {model_id}   {simple_date(created)}"))
        print()

        while True:
            picked_model = input("Model: ").strip()
            if picked_model in [model[0] for model in openai_models]:
                return picked_model
            else:
                print(colors.red(f"\nModel {picked_model} is NOT a supported model by OpenAI. Please try again!\n"))

    except Exception as e:
        print(colors.red(f"An error occurred while fetching models: {e}"))
        sys.exit(1)

def get_user_input(prompt_text, validation_func=lambda x: True, error_message="Invalid input. Please try again."):
    while True:
        user_input = input(prompt_text).strip()
        if validation_func(user_input):
            return user_input
        else:
            print(error_message)

def save_url_img(filepath, url):
    try:
        image_data = requests.get(url).content
        with open(filepath, 'wb') as handler:
            handler.write(image_data)
    except Exception as e:
        print(colors.red(f"Failed to grab image: {e}"))

def main():
    try:
        model = pick_img_model()
        prompt = get_user_input("Prompt: ")
        quality = get_user_input("Quality (standard/hd): ", lambda x: x.lower() in ["standard", "hd"], colors.red("\nPlease enter 'standard' or 'hd' for quality\n"))
        n = get_user_input("N (number of images): ", lambda x: x.isdigit() and int(x) > 0, colors.red("\nPlease enter a positive integer\n"))
        size = get_user_input("Size (WidthxHeight): ", lambda x: 'x' in x and all(num.isdigit() for num in x.split('x')), colors.red("\nPlease enter size in format WidthxHeight (e.g., 1024x1024)\n"))
    except:
        print(colors.red(f"\nError occurred well getting user input for image generation"))
        sys.exit(1)

    try:
        response = client.images.generate(model=model, prompt=prompt, size=size, quality=quality, n=int(n))
        for i, data in enumerate(response.data):
            url = data.url
            filename = img_filename(model, prompt)
            save_url_img(filename, url)
            print(colors.blue(f"\nCreated Image: {filename}"))
    except Exception as e:
        print(colors.red(f"Failed to generate image: {e}"))

if __name__ == "__main__":
    main()

