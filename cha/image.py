import subprocess
import requests
import time
import json
import sys
import os

from io import BytesIO
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from cha import colors, utils, config


def display_metadata(image_path):
    try:
        if image_path.startswith("ig_") == False or os.path.isfile(image_path) == False:
            raise Exception(f"Invalid image path provided")
        data = None
        with Image.open(image_path) as img:
            data = img.info
        print(colors.green(f"Image:"), image_path)
        print(colors.green(f"MetaData:"))
        print(json.dumps(data, indent=4))
        return data
    except IOError:
        print(colors.red("Failed to load image file"))
        return None
    except Exception as e:
        print(colors.red(f"{e}"))
        return None


def gen_img_filename(model, s):
    filtered_chars = "".join(filter(lambda c: c.isalpha() or c.isspace(), s))
    filtered_chars = filtered_chars.lower()
    content = [
        "ig_",
        model.lower(),
        "_",
        utils.generate_short_uuid(),
        ".jpg",
    ]
    return "".join(content)


def pick_img_model(client):
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
            print(colors.yellow(f"   > {model_id}   {utils.simple_date(created)}"))

        while True:
            picked_model = input(colors.blue("Model: ")).strip()
            if picked_model in [model[0] for model in openai_models]:
                return picked_model
            else:
                print(
                    colors.red(
                        f"Model {picked_model} is NOT a supported model by OpenAI. Please try again!"
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


def get_user_open(filepaths):
    option = None
    while True:
        user_input = input(colors.magenta("Open The Files (y/n)? ")).lower()
        if user_input in ["yes", "y"]:
            option = True
            break
        elif user_input in ["no", "n"]:
            option = False
            break
        else:
            print(colors.red("Invalid input. Please enter yes, no, y, or n"))

    if option == True:
        for filepath in filepaths:
            open_file_default_app(filepath)


def gen_image(client):
    try:
        model = pick_img_model(client)
        prompt = get_user_input(colors.blue("Prompt: "))
        quality = get_user_input(
            colors.blue("Quality (standard/hd): "),
            lambda x: x.lower() in ["standard", "hd"],
            colors.red("Please enter 'standard' or 'hd' for quality"),
        )
        n = get_user_input(
            colors.blue("N (number of images): "),
            lambda x: x.isdigit() and int(x) > 0,
            colors.red("Please enter a positive integer"),
        )
        size = get_user_input(
            colors.blue("Size (WidthxHeight): "),
            lambda x: x in config.COMMON_IMG_GEN_RESOLUTIONS,
            colors.red(
                f"Valid Size(s): {', '.join(config.COMMON_IMG_GEN_RESOLUTIONS)}"
            ),
        )
    except:
        print(
            colors.red(
                f"\nError occurred while getting user input for image generation"
            )
        )
        sys.exit(1)

    try:
        params = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": int(n),
        }

        response = client.images.generate(**params)
        url = response.data[0].url

        img_filename = gen_img_filename(model, prompt)
        img_data = utils.get_request(url)
        if img_data == None:
            print(colors.red(f"Failed to get image from {url}"))
            return
        img_data = img_data.content

        # save config/meta_data to image
        with Image.open(BytesIO(img_data)) as img:
            metadata = PngInfo()
            metadata.add_text("Prompt", prompt)
            metadata.add_text("Model", model)
            metadata.add_text("Quality", quality)
            metadata.add_text("Size", size)
            metadata.add_text("Created", str(time.time()))
            img.save(img_filename, "PNG", pnginfo=metadata)

        print(colors.green(f"Created Image:"), img_filename)
        print(colors.yellow(f"To View MetaData:"), "cha -igmd <image_path>")

        get_user_open([img_filename])
    except Exception as e:
        print(colors.red(f"Failed to generate image: {e}"))
