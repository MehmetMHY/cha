from pydantic import BaseModel
import importlib
import copy

from cha import scraper, utils, config, colors, loading


def brute_force_models_list(client, url, headers, model_name, clean, models_info):
    json_name_path = models_info.get("json_name_path")

    raw_response = utils.get_request(url=url, headers=headers)
    content_data = raw_response.text

    if json_name_path is not None:
        content_data = raw_response.json()

    if isinstance(content_data, list) and json_name_path:
        dict_path = json_name_path.split(".")
        # NOTE: if deeper nesting is needed, you can expand logic here (dict_path[1], etc.)
        if len(dict_path) == 1:
            field = dict_path[0]
            model_ids = []
            for entry in content_data:
                if isinstance(entry, dict) and field in entry:
                    model_ids.append(entry[field])
            return sorted(set(model_ids))

    if isinstance(content_data, dict):
        try:
            dict_path = json_name_path.split(".")
            tmp = copy.deepcopy(content_data)
            model_name_key = None
            if len(dict_path) > 1:
                for i in range(len(dict_path)):
                    key = dict_path[i]
                    if not isinstance(tmp[key], list):
                        tmp = tmp[key]
                    else:
                        tmp = tmp[key]
                        model_name_key = dict_path[i + 1]
                        break
            else:
                model_name_key = dict_path[0]

            output = []
            for entry in tmp:
                output.append(entry[model_name_key])
            output = list(set(output))
            output.sort()
            return output
        except Exception as e:
            pass

    raw_content = str(content_data)
    if clean:
        raw_content = scraper.remove_html(raw_content)

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


def auto_select_a_platform(client, platform_key=None, model_name=None):
    if platform_key is None or platform_key not in config.THIRD_PARTY_PLATFORMS.keys():
        print(colors.yellow("Available platforms:"))
        for index, platform in enumerate(config.THIRD_PARTY_PLATFORMS.keys(), start=1):
            print(colors.yellow(f"   {index}) {platform}"))
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

    models_list = []
    final_model = model_name
    if model_name is None:
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
                models_info=models_info,
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
            print(colors.yellow(f"   {idx}) {model}"))
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
