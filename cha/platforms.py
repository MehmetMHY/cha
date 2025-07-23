import subprocess
import copy

from cha import utils, config, colors, loading
from cha.client import get_current_chat_client


def list_models():
    if config.CHA_CURRENT_PLATFORM_NAME == "openai":
        response = get_current_chat_client().models.list()
        if not response.data:
            raise ValueError("No models available")

        models = []
        for model in response.data:
            if (
                any(substr in model.id for substr in config.OPENAI_MODELS_TO_KEEP)
                and not any(
                    substr in model.id for substr in config.OPENAI_MODELS_TO_IGNORE
                )
                and (
                    not getattr(config, "OPENAI_IGNORE_DATED_MODEL_NAMES", False)
                    or not utils.contains_date(model.id)
                )
            ):
                models.append([model.id, model.created])

        models = sorted(models, key=lambda x: x[1])
        provided_models = []
        for model in models:
            provided_models.append(model[0])
    else:
        platform_config = config.THIRD_PARTY_PLATFORMS[config.CHA_CURRENT_PLATFORM_NAME]
        provided_models = get_platform_model_list(
            url=platform_config["models"]["url"],
            headers=platform_config["models"]["headers"],
            models_info=platform_config["models"],
        )

    if not provided_models:
        print(colors.red("No models available to select"))
        return None

    fzf_prompt = f"Select a {config.CHA_CURRENT_PLATFORM_NAME.upper()} model: "
    try:
        selected_model = utils.run_fzf_ssh_safe(
            ["fzf", "--reverse", "--height=40%", "--border", f"--prompt={fzf_prompt}"],
            "\n".join(provided_models),
        )
        return selected_model if selected_model else None
    except (subprocess.CalledProcessError, subprocess.SubprocessError):
        return None


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
    all_platforms = ["openai"] + list(config.THIRD_PARTY_PLATFORMS.keys())
    if platform_key is None or platform_key not in all_platforms:
        try:
            from cha import utils

            platform_key = utils.run_fzf_ssh_safe(
                [
                    "fzf",
                    "--reverse",
                    "--height=40%",
                    "--border",
                    "--prompt=Select a platform: ",
                ],
                "\n".join(all_platforms),
            )
            if not platform_key:
                return None
        except (subprocess.CalledProcessError, subprocess.SubprocessError):
            return None

    if platform_key == "openai":
        from cha.client import set_current_chat_client

        config.CHA_CURRENT_PLATFORM_NAME = "openai"
        set_current_chat_client(api_key=None, base_url=None)

        final_model = model_name
        if final_model is None:
            final_model = list_models()

        if not final_model:
            return None

        return {
            "env_name": "OPENAI_API_KEY",
            "base_url": None,
            "picked_model": final_model,
            "platform_name": "openai",
        }

    config.CHA_CURRENT_PLATFORM_NAME = platform_key
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
            from cha import utils

            final_model = utils.run_fzf_ssh_safe(
                [
                    "fzf",
                    "--reverse",
                    "--height=40%",
                    "--border",
                    "--prompt=Select a model: ",
                ],
                "\n".join(models_list),
            )
            if not final_model:
                return None
        except (subprocess.CalledProcessError, subprocess.SubprocessError):
            return None

    output = copy.deepcopy(config.THIRD_PARTY_PLATFORMS[platform_key])
    output["models"] = models_list
    output["picked_model"] = final_model
    output["platform_name"] = platform_key

    return output
