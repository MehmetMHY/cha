import tiktoken


def tokens_counter(model_name: str, string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding_name = tiktoken.encoding_for_model(model_name)
    encoding = tiktoken.get_encoding(encoding_name.name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def text_model_pricing(model):
    """
    UPDATED: May 13, 2024
    SOURCE: https://openai.com/pricing
    NOTES:
        - The pricings are for every 1 Million tokens
        - We only account for text based model
        - We ignore image models, for now
        - The cost is in dollars ($)
    """
    token_per_count = 1_000_000
    text_models = {
        "gpt-4o": {"input": 5.00, "output": 15.00},
        "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-4-turbo-2024-04-09": {"input": 10.00, "output": 30.00},
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-32k": {"input": 60.00, "output": 120.00},
        "gpt-3.5-turbo-0125": {"input": 0.50, "output": 1.50},
        "gpt-3.5-turbo-instruct": {"input": 1.50, "output": 2.00},
        "gpt-4-0125-preview": {"input": 10.00, "output": 30.00},
        "gpt-4-1106-preview": {"input": 10.00, "output": 30.00},
        "gpt-4-vision-preview": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo-1106": {"input": 1.00, "output": 2.00},
        "gpt-3.5-turbo-0613": {"input": 1.50, "output": 2.00},
        "gpt-3.5-turbo-16k-0613": {"input": 3.00, "output": 4.00},
        "gpt-3.5-turbo-0301": {"input": 1.50, "output": 2.00},
    }

    pricing = text_models.get(model)

    if pricing != None:
        pricing["official"] = True
        pricing["div_by"] = token_per_count
        return pricing

    all_values = [info[key] for model, info in text_models.items() for key in info]
    return {
        "official": False,
        "low": min(all_values),
        "high": max(all_values),
        "div_by": token_per_count,
    }


def totals_costs_cal_and_print(selected_model, total_user_text, total_bot_text):
    try:
        user_tokens = tokens_counter(selected_model, total_user_text)
        bot_tokens = tokens_counter(selected_model, total_bot_text)
    except:
        # NOTE: just used hard-coded model for token estimate
        user_tokens = tokens_counter("gpt-4", total_user_text)
        bot_tokens = tokens_counter("gpt-4", total_bot_text)

    user_cost = 0
    bot_cost = 0
    pricing = text_model_pricing(selected_model)
    div = pricing["div_by"]
    if pricing["official"] == True:
        user_cost = (user_tokens / div) * pricing["input"]
        bot_cost = (bot_tokens / div) * pricing["output"]
    else:
        # NOTE: really estimate the pricing for models that are not listed/saved
        est_avg_price = ((pricing["high"] + pricing["low"]) / 2) * 1.2
        user_cost = (user_tokens / div) * est_avg_price
        bot_cost = (bot_tokens / div) * est_avg_price

    stats = {
        "model_name": selected_model,
        "input_tokens": user_tokens,
        "output_tokens": bot_tokens,
        "total_tokens": user_tokens + bot_tokens,
        "input_cost": user_cost,
        "output_cost": bot_cost,
        "total_cost": user_cost + bot_cost,
    }

    return stats
