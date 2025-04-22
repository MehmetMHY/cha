# Cha Weather Tool

This is a weather information tool for [Cha](https://github.com/MehmetMHY/cha/) that retrieves and displays the user's current weather stats using [wttr.in](https://wttr.in/).

## Features

- Fetches up-to-date weather stats in JSON from wttr.in
- Answers user questions about the weather using Cha's tool interface
- Can be called with the alias `!weather`
- User input (question) is piped into the tool for contextual answers

## Usage

### Within Cha

1. Integrate this tool into your `.cha/tools/weather/` directory.
2. You can invoke the tool in Cha chat using the alias:

   ```
   !weather <your weather question>
   ```

   **Example:**

   ```
   !weather will it be sunny today?
   ```

3. The tool will fetch current weather data and answer your question accordingly.

### As Standalone

Run the script directly:

```shell
python main.py
```

Follow the prompt to enter your weather-related query, starting with `!weather`, for example:

```
!weather Is it raining right now?
```

## Options

- **Alias**: `!weather`
- **Includes chat history**: No (does not include prior chat by default)
- **User input piped**: Yes (your query is passed to the tool)
- **Output piped to chat**: Yes (tool output is returned as the assistant's reply)
- **Timeout**: 30 seconds

## Requirements

- [Cha](https://github.com/MehmetMHY/cha/)
- Python 3.7+
- `requests` library (for HTTP requests). Install via `pip install requests` if needed.
