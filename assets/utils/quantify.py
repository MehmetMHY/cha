from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
import json
import math
import os

from cha import colors, utils

MODELS_COSTS = {"currency": "$", "per": 1_000_000, "units": "tokens", "models": []}
with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "costs.json"), "r"
) as file:
    ALL_PLATFORM_COSTS = json.load(file)
for platform in ALL_PLATFORM_COSTS:
    for model in ALL_PLATFORM_COSTS[platform]:
        values = ALL_PLATFORM_COSTS[platform][model]
        try:
            MODELS_COSTS["models"].append(
                {
                    "model": model,
                    "input": float(values.get("input")),
                    "output": float(values.get("output")),
                }
            )
        except:
            continue


def get_folder_size_mb(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)


def cha_stats():
    average_input_token_price = (
        math.ceil(
            sum(m["input"] for m in MODELS_COSTS["models"])
            / len(MODELS_COSTS["models"])
        )
        if MODELS_COSTS["models"]
        else 0.0
    )

    average_output_token_price = (
        math.ceil(
            sum(m["output"] for m in MODELS_COSTS["models"])
            / len(MODELS_COSTS["models"])
        )
        if MODELS_COSTS["models"]
        else 0.0
    )

    cha_hs_dir = os.path.join(str(Path.home()), ".cha", "history")

    history = {}
    for filename in os.listdir(cha_hs_dir):
        if os.path.isfile(os.path.join(cha_hs_dir, filename)):
            filename = os.path.join(cha_hs_dir, filename)
            if filename.endswith(".json"):
                try:
                    with open(filename) as f:
                        data = json.load(f)
                    name = filename.split("/")[-1]
                    history[name] = data
                except Exception as e:
                    continue

    total_conversation_duration_seconds = 0.0
    oldest_time = None
    latest_time = None
    user_prompts = []
    bot_responses = []
    longest_chat = 0
    models_used = []

    for key in history:
        models_used.append(history[key]["args"]["model"])

        current_chat_exchanges = history[key].get("chat", [])
        if not isinstance(current_chat_exchanges, list):
            current_chat_exchanges = []

        if len(current_chat_exchanges) > longest_chat:
            longest_chat = len(current_chat_exchanges)

        conversation_start_time_for_key = None
        conversation_end_time_for_key = None

        sys_prompt_cycle_for_key = True

        for exchange in current_chat_exchanges:
            if "time" not in exchange:
                continue

            time_value = exchange["time"]

            if (
                conversation_start_time_for_key is None
                or time_value < conversation_start_time_for_key
            ):
                conversation_start_time_for_key = time_value

            if (
                conversation_end_time_for_key is None
                or time_value > conversation_end_time_for_key
            ):
                conversation_end_time_for_key = time_value

            if sys_prompt_cycle_for_key:
                sys_prompt_cycle_for_key = False
            else:
                if "user" in exchange:
                    user_prompts.append(exchange["user"])
                if "bot" in exchange:
                    bot_responses.append(exchange["bot"])

            if oldest_time is None or time_value < oldest_time:
                oldest_time = time_value

            if latest_time is None or time_value > latest_time:
                latest_time = time_value

        if (
            conversation_start_time_for_key is not None
            and conversation_end_time_for_key is not None
        ):
            duration_this_key = (
                conversation_end_time_for_key - conversation_start_time_for_key
            )
            total_conversation_duration_seconds += duration_this_key

    longest_chat = longest_chat * 2

    avg_user_prompt_len = (
        sum(len(p) for p in user_prompts if p is not None)
        / len([p for p in user_prompts if p is not None])
        if user_prompts and any(p is not None for p in user_prompts)
        else 0.0
    )

    avg_bot_response_len = (
        sum(len(r) for r in bot_responses if r is not None)
        / len([r for r in bot_responses if r is not None])
        if bot_responses and any(r is not None for r in bot_responses)
        else 0.0
    )

    days_passed = 0.0
    if (
        oldest_time is not None
        and latest_time is not None
        and latest_time >= oldest_time
    ):
        days_passed = (latest_time - oldest_time) / (60 * 60 * 24)

    avg_chats_per_day = (
        (len(history) / days_passed)
        if days_passed > 0
        else (float(len(history)) if len(history) > 0 and days_passed == 0.0 else 0.0)
    )

    num_conversations = len(history)
    avg_time_per_conversation_seconds = (
        (total_conversation_duration_seconds / num_conversations)
        if num_conversations > 0
        else 0.0
    )

    total_input_tokens = sum(
        utils.count_tokens(text=p, model_name=None, fast_mode=True)
        for p in user_prompts
        if p is not None
    )

    total_output_tokens = sum(
        utils.count_tokens(text=r, model_name=None, fast_mode=True)
        for r in bot_responses
        if r is not None
    )

    model_price_lookup = {m["model"]: m for m in MODELS_COSTS["models"]}

    total_cost = 0.0
    thirty_days_ago_ts = datetime.now(timezone.utc).timestamp() - (30 * 24 * 60 * 60)
    seven_days_ago_ts = datetime.now(timezone.utc).timestamp() - (7 * 24 * 60 * 60)
    cost_last_month = 0.0
    cost_last_week = 0.0
    days_with_chats_in_last_month = set()
    days_with_chats_in_last_week = set()

    for key in history:
        model_name = history[key]["args"]["model"]
        current_chat_exchanges = history[key].get("chat", [])
        if not isinstance(current_chat_exchanges, list):
            current_chat_exchanges = []

        user_texts = []
        bot_texts = []
        sys_prompt_cycle_for_key = True
        latest_chat_time = None
        for exchange in current_chat_exchanges:
            if "time" in exchange:
                if latest_chat_time is None or exchange["time"] > latest_chat_time:
                    latest_chat_time = exchange["time"]

            if sys_prompt_cycle_for_key:
                sys_prompt_cycle_for_key = False
                continue
            if "user" in exchange:
                user_texts.append(exchange["user"])
            if "bot" in exchange:
                bot_texts.append(exchange["bot"])

        input_tokens = sum(
            utils.count_tokens(text=p, model_name=None, fast_mode=True)
            for p in user_texts
            if p is not None
        )
        output_tokens = sum(
            utils.count_tokens(text=r, model_name=None, fast_mode=True)
            for r in bot_texts
            if r is not None
        )

        model_info = model_price_lookup.get(model_name, None)
        input_price = model_info["input"] if model_info else average_input_token_price
        output_price = (
            model_info["output"] if model_info else average_output_token_price
        )

        cost = (
            input_tokens * input_price + output_tokens * output_price
        ) / MODELS_COSTS["per"]
        total_cost += cost

        if latest_chat_time and latest_chat_time >= thirty_days_ago_ts:
            cost_last_month += cost
            days_with_chats_in_last_month.add(
                datetime.fromtimestamp(latest_chat_time, tz=timezone.utc).date()
            )

        if latest_chat_time and latest_chat_time >= seven_days_ago_ts:
            cost_last_week += cost
            days_with_chats_in_last_week.add(
                datetime.fromtimestamp(latest_chat_time, tz=timezone.utc).date()
            )

    # NOTE: start printing final results

    spacing_value = 21
    print(
        f"{colors.green('Current Timestamp:'.ljust(spacing_value))} {colors.red(datetime.now(timezone.utc).strftime('%b %d, %Y %H:%M:%S')[:23] + ' (24H) UTC')}"
    )

    most_used = Counter(models_used).most_common(1)[0] if models_used else ("None", 0)
    print(
        f"{colors.green('Most Popular Model:'.ljust(spacing_value))} {colors.blue(most_used[0])} {colors.green(f'({most_used[1]} times)')}"
    )

    print(
        f"{colors.green('Total Days Passed:'.ljust(spacing_value))} {colors.yellow(f'{round(days_passed, 2)} days')}"
    )
    print(
        f"{colors.green('Oldest Timestamp:'.ljust(spacing_value))} {colors.yellow(str(round(oldest_time, 2) if oldest_time is not None and isinstance(oldest_time, (float, int)) else oldest_time) + ' seconds')}"
    )
    print(
        f"{colors.green('Newest Timestamp:'.ljust(spacing_value))} {colors.yellow(str(round(latest_time, 2) if latest_time is not None and isinstance(latest_time, (float, int)) else latest_time) + ' seconds')}"
    )

    print(
        f"{colors.green('Total Chat Sessions:'.ljust(spacing_value))} {colors.red(f'{len(history):,} chats')}"
    )
    print(
        f"{colors.green('Longest Chat Session:'.ljust(spacing_value))} {colors.yellow(f'{longest_chat} messages')}"
    )
    print(
        f"{colors.green('Avg Chats Per Day:'.ljust(spacing_value))} {colors.yellow(str(math.ceil(avg_chats_per_day)))} {colors.yellow('chats')}"
    )

    print(
        f"{colors.green('Avg User Prompt Len:'.ljust(spacing_value))} {colors.yellow(f'{round(avg_user_prompt_len, 2)} chars')}"
    )
    print(
        f"{colors.green('Avg Bot Response Len:'.ljust(spacing_value))} {colors.yellow(f'{round(avg_bot_response_len, 2)} chars')}"
    )

    print(
        f"{colors.green('Avg Chat Duration:'.ljust(spacing_value))} {colors.yellow(f'{round(avg_time_per_conversation_seconds, 2)} seconds')}"
    )

    print(
        f"{colors.green('Total Input Tokens:'.ljust(spacing_value))} {colors.yellow(f'{total_input_tokens:,} tokens')}"
    )
    print(
        f"{colors.green('Total Output Tokens:'.ljust(spacing_value))} {colors.yellow(f'{total_output_tokens:,} tokens')}"
    )

    # token/cost analytics
    avg_tokens_per_chat = (
        (total_input_tokens + total_output_tokens) / len(history) if history else 0
    )
    print(
        f"{colors.green('Avg Tokens Per Chat:'.ljust(spacing_value))} {colors.yellow(f'{int(avg_tokens_per_chat):,} tokens')}"
    )

    token_efficiency = (
        total_output_tokens / total_input_tokens if total_input_tokens > 0 else 0
    )
    print(
        f"{colors.green('Output/Input Ratio:'.ljust(spacing_value))} {colors.yellow(f'{token_efficiency:.2f}x')}"
    )

    avg_cost_per_chat = total_cost / len(history) if history else 0
    print(
        f"{colors.green('Avg Cost Per Chat:'.ljust(spacing_value))} {colors.red(f'${avg_cost_per_chat:.3f}')}"
    )

    # find most expensive chat
    most_expensive_chat = {"cost": 0, "id": None}
    for key in history:
        model_name = history[key]["args"]["model"]
        current_chat_exchanges = history[key].get("chat", [])
        if not isinstance(current_chat_exchanges, list):
            continue

        user_texts = []
        bot_texts = []
        sys_prompt_cycle_for_key = True
        for exchange in current_chat_exchanges:
            if sys_prompt_cycle_for_key:
                sys_prompt_cycle_for_key = False
                continue
            if "user" in exchange:
                user_texts.append(exchange["user"])
            if "bot" in exchange:
                bot_texts.append(exchange["bot"])

        input_tokens = sum(
            utils.count_tokens(text=p, model_name=None, fast_mode=True)
            for p in user_texts
            if p is not None
        )
        output_tokens = sum(
            utils.count_tokens(text=r, model_name=None, fast_mode=True)
            for r in bot_texts
            if r is not None
        )

        model_info = model_price_lookup.get(model_name, None)
        input_price = model_info["input"] if model_info else average_input_token_price
        output_price = (
            model_info["output"] if model_info else average_output_token_price
        )

        chat_cost = (
            input_tokens * input_price + output_tokens * output_price
        ) / MODELS_COSTS["per"]
        if chat_cost > most_expensive_chat["cost"]:
            most_expensive_chat = {"cost": chat_cost, "id": key}

    if most_expensive_chat["id"]:
        exp_cost = most_expensive_chat["cost"]
        exp_id = most_expensive_chat["id"]
        exp_id_clean = exp_id.replace(".json", "")
        print(
            f"{colors.green('Most Expensive Chat:'.ljust(spacing_value))} {colors.red(f'${exp_cost:.2f}')} {colors.blue(f'({exp_id_clean})')}"
        )

    print(
        f"{colors.green('Estimated Total Cost:'.ljust(spacing_value))} {colors.red(f'${total_cost:.2f}')}"
    )

    days_in_last_month = len(days_with_chats_in_last_month)
    if days_in_last_month > 0:
        estimated_monthly_cost = (cost_last_month / days_in_last_month) * 30
        print(
            f"{colors.green('Est. Cost Per Month:'.ljust(spacing_value))} {colors.blue(f'${estimated_monthly_cost:.2f}')}"
        )

    days_in_last_week = len(days_with_chats_in_last_week)
    if days_in_last_week > 0:
        estimated_weekly_cost = (cost_last_week / days_in_last_week) * 7
        print(
            f"{colors.green('Est. Cost Per Week:'.ljust(spacing_value))} {colors.blue(f'${estimated_weekly_cost:.2f}')}"
        )

    print(
        f"{colors.green('Average Cost Per Day:'.ljust(spacing_value))} {colors.red(f'${total_cost / days_passed:.2f}')}"
    )

    print(
        f"{colors.green('Total History Size:'.ljust(spacing_value))} {colors.yellow(f'{get_folder_size_mb(cha_hs_dir):.2f} MB')}"
    )

    return


if __name__ == "__main__":
    cha_stats()
