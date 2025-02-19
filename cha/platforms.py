from pydantic import BaseModel
import copy

from cha import scraper, utils, config, colors, loading


def brute_force_models_list(client, url, headers, model_name, clean):
    raw_response = utils.get_request(url=url, headers=headers)
    content_data = raw_response.text
    raw_content = content_data
    if clean:
        raw_content = scraper.remove_html(content_data)

    class ModelNames(BaseModel):
        names: list[str]

    completion = client.beta.chat.completions.parse(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "Given text from a web scrape, extract the model id(s) the API supports",
            },
            {
                "role": "user",
                "content": raw_content,
            },
        ],
        response_format=ModelNames,
    )

    return completion.choices[0].message.parsed.names


def auto_select_a_platform(client):
    print(colors.yellow("Available platforms:"))
    for index, platform in enumerate(config.THIRD_PARTY_PLATFORMS.keys(), start=1):
        print(colors.yellow(f"  {index}. {platform}"))
    while True:
        try:
            choice = int(utils.safe_input(colors.blue("Select a platform: ")))
            if 1 <= choice <= len(config.THIRD_PARTY_PLATFORMS):
                break
            raise Exception(f"Invalid input selected")
        except ValueError:
            print(colors.red("Please enter a valid number"))

    platform_key = list(config.THIRD_PARTY_PLATFORMS.keys())[choice - 1]
    selected_platform = config.THIRD_PARTY_PLATFORMS[platform_key]

    models_info = selected_platform["models"]
    url = models_info["url"]
    headers = models_info["headers"]

    rm_html = False
    if models_info.get("clean") == True:
        rm_html = True

    failed_to_get_models = False
    try:
        loading.start_loading("Getting Model Names", "dots")
        models_list = brute_force_models_list(
            client=client,
            url=url,
            headers=headers,
            model_name=config.SCRAPE_MODEL_NAME_FOR_PLATFORMS,
            clean=rm_html,
        )
    except Exception as e:
        loading.print_message(colors.red(f"Failed to retrieve model: {e}"))
        failed_to_get_models = True
    finally:
        loading.stop_loading()

    if failed_to_get_models:
        return

    if not models_list or not isinstance(models_list, list):
        print(colors.red("No models found or returned in an unexpected format"))
        return

    print(colors.yellow("Available models:"))
    for idx, model in enumerate(models_list, start=1):
        print(colors.yellow(f"  {idx}. {model}"))
    while True:
        try:
            model_choice = int(utils.safe_input(colors.blue("Select a model: ")))
            if 1 <= model_choice <= len(models_list):
                break
            raise Exception(f"Invalid input selected")
        except ValueError:
            print(colors.red("Please enter a valid number"))

    final_model = models_list[model_choice - 1]
    output = copy.deepcopy(config.THIRD_PARTY_PLATFORMS[platform_key])
    output["models"] = models_list
    output["picked_model"] = final_model

    return output
