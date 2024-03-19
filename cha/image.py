import subprocess
import requests
import datetime
import shutil
import json
import time
import sys

# 3rd party packages
from openai import OpenAI
from cha import colors

client = OpenAI()


def img_filename(model, s, max_word=10):
    filtered_chars = "".join(filter(lambda c: c.isalpha() or c.isspace(), s))
    filtered_chars = filtered_chars.lower()
    content = [
        model.lower(),
        "__",
        str(int(time.time())),
        "__",
        "_".join(filtered_chars.split(" ")[:max_word]),
        ".jpg",
    ]
    return "".join(content)


def simple_date(epoch_time):
    date_time = datetime.datetime.fromtimestamp(epoch_time)
    return date_time.strftime("%B %d, %Y")


def pick_img_model():
    try:
        response = client.models.list()
        if not response.data:
            print(colors.red("No models available. Exiting..."))
            sys.exit(1)

        openai_models = [
            (model.id, model.created) for model in response.data if "dall" in model.id
        ]
        openai_models = sorted(openai_models, key=lambda x: x[1], reverse=True)

        print(colors.yellow("Available OpenAI Models:"))
        for model_id, created in openai_models:
            print(colors.yellow(f"   > {model_id}   {simple_date(created)}"))
        print()

        while True:
            picked_model = input(colors.blue("Model: ")).strip()
            if picked_model in [model[0] for model in openai_models]:
                return picked_model
            else:
                print(
                    colors.red(
                        f"\nModel {picked_model} is NOT a supported model by OpenAI. Please try again!\n"
                    )
                )

    except Exception as e:
        print(colors.red(f"An error occurred while fetching models: {e}"))
        sys.exit(1)


def get_user_input(
    prompt_text,
    validation_func=lambda x: True,
    error_message="Invalid input. Please try again.",
):
    while True:
        user_input = input(prompt_text).strip()
        if validation_func(user_input):
            return user_input
        else:
            print(error_message)


def save_url_img(filepath, url):
    try:
        image_data = requests.get(url).content
        with open(filepath, "wb") as handler:
            handler.write(image_data)
    except Exception as e:
        print(colors.red(f"Failed to grab image: {e}"))


def open_file_default_app(filepath):
    try:
        if sys.platform.startswith("linux"):
            subprocess.run(["xdg-open", filepath], check=True)
        elif sys.platform == "darwin":
            subprocess.run(["open", filepath], check=True)
        elif sys.platform == "win32":
            subprocess.run(["start", filepath], shell=True, check=True)
        else:
            print(colors.red("OS is not supported"))
    except Exception as e:
        print(colors.red(f"Failed to open file: {e}"))


def get_user_open(filepath):
    option = None
    while True:
        user_input = input(colors.yellow("Open The Image (y/n)? ")).lower()
        if user_input in ["yes", "y"]:
            option = True
            break
        elif user_input in ["no", "n"]:
            option = False
            break
        else:
            print(colors.red("\nInvalid input. Please enter yes, no, y, or n.\n"))

    if option == True:
        open_file_default_app(filepath)


def gen_image():
    try:
        model = pick_img_model()
        prompt = get_user_input(colors.blue("Prompt: "))
        quality = get_user_input(
            colors.blue("Quality (standard/hd): "),
            lambda x: x.lower() in ["standard", "hd"],
            colors.red("\nPlease enter 'standard' or 'hd' for quality\n"),
        )
        n = get_user_input(
            colors.blue("N (number of images): "),
            lambda x: x.isdigit() and int(x) > 0,
            colors.red("\nPlease enter a positive integer\n"),
        )
        size = get_user_input(
            colors.blue("Size (WidthxHeight): "),
            lambda x: "x" in x and all(num.isdigit() for num in x.split("x")),
            colors.red(
                "\nPlease enter size in format WidthxHeight (e.g., 1024x1024)\n"
            ),
        )
    except:
        print(
            colors.red(f"\nError occurred well getting user input for image generation")
        )
        sys.exit(1)

    try:
        response = client.images.generate(
            model=model, prompt=prompt, size=size, quality=quality, n=int(n)
        )
        url = response.data[0].url
        filename = img_filename(model, prompt)
        save_url_img(filename, url)

        print(colors.green(f"\nCreated Image:"))
        print(f"{filename}\n")

        # display generated image in the termianl using CLImage (https://github.com/MehmetMHY/CLImage)
        try:
            import climage

            print(
                climage.convert(
                    filename,
                    is_unicode=False,
                    width=int(shutil.get_terminal_size().columns * 0.7),
                )
            )
        except:
            pass

        get_user_open(filename)
    except Exception as e:
        print(colors.red(f"Failed to generate image: {e}"))
