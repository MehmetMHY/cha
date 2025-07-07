import subprocess
import copy

from cha import utils, config, colors, loading


def get_platform_model_list(url, headers, models_info):
    json_name_path = models_info.get("json_name_path")

    raw_response = utils.get_request(url=url, headers=headers)
    content_data = raw_response.json()

    if isinstance(content_data, list) and json_name_path:
        dict_path = json_name_path.split(".")
        # when deeper nesting is needed, you can expand logic here (dict_path[1], etc.)
        if len(dict_path) == 1:
            field = dict_path[0]
            model_ids = []
            for entry in content_data:
                if isinstance(entry, dict) and field in entry:
                    model_ids.append(entry[field])
            return sorted(set(model_ids))

    if isinstance(content_data, dict):
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

    raise Exception(f"Failed to retrieve model list from {url}")


def auto_select_a_platform(platform_key=None, model_name=None):
    if platform_key is None or platform_key not in config.THIRD_PARTY_PLATFORMS.keys():
        try:
            platforms = list(config.THIRD_PARTY_PLATFORMS.keys())
            fzf_process = subprocess.run(
                [
                    "fzf",
                    "--reverse",
                    "--height=40%",
                    "--border",
                    "--prompt=Select a platform: ",
                ],
                input="\n".join(platforms).encode(),
                capture_output=True,
                check=True,
            )
            platform_key = fzf_process.stdout.decode().strip()
            if not platform_key:
                print(colors.red("No platform selected"))
                return None
        except (subprocess.CalledProcessError, subprocess.SubprocessError):
            return None

    selected_platform = config.THIRD_PARTY_PLATFORMS[platform_key]

    models_list = []
    final_model = model_name
    if model_name is None:
        models_info = selected_platform["models"]
        url = models_info["url"]
        headers = models_info["headers"]

        failed_to_get_models = False
        try:
            loading.start_loading("Getting Model Names", "dots")
            models_list = get_platform_model_list(
                url=url,
                headers=headers,
                models_info=models_info,
            )
        except Exception as e:
            loading.print_message(colors.red(f"Failed to retrieve model: {e}"))
            failed_to_get_models = True
        finally:
            loading.stop_loading()

        if failed_to_get_models:
            return None

        if not models_list or not isinstance(models_list, list):
            print(colors.red("No models found or returned in an unexpected format"))
            return None

        try:
            fzf_process = subprocess.run(
                [
                    "fzf",
                    "--reverse",
                    "--height=40%",
                    "--border",
                    "--prompt=Select a model: ",
                ],
                input="\n".join(models_list).encode(),
                capture_output=True,
                check=True,
            )
            final_model = fzf_process.stdout.decode().strip()
            if not final_model:
                print(colors.red("No model selected"))
                return None
        except (subprocess.CalledProcessError, subprocess.SubprocessError):
            return None

    output = copy.deepcopy(config.THIRD_PARTY_PLATFORMS[platform_key])
    output["models"] = models_list
    output["picked_model"] = final_model
    output["platform_name"] = platform_key

    return output
