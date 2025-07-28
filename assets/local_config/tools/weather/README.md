# Cha Weather Tool

This is a weather information tool for [Cha](https://github.com/MehmetMHY/cha/) that retrieves and displays the user’s current weather stats using [wttr.in](https://wttr.in/).

## Features

- Fetches up-to-date weather stats in JSON from wttr.in
- Answers user questions about the weather using Cha's tool interface
- Can be called with the alias `!weather`
- User input (question) and most recent chat history are piped into the tool for contextual answers

## Usage

### Within Cha

Integrate this tool into your `.cha/tools/weather/` directory.  
You can invoke the tool in Cha chat using the alias:

```
!weather <your weather question>
```

**Example:**

```
!weather will it be sunny today?
```

The tool will fetch current weather data and answer your question accordingly, taking into account your question and up to two of your most recent chat messages.

### As Standalone

Run the script directly from the terminal:

```shell
python main.py
```

Follow the prompt to enter your weather-related query, starting with `!weather`, for example:

```
!weather Is it raining right now?
```

## Options / Integration Details

- **Alias**: `!weather`
- **Includes chat history**: Yes (uses up to the last 2 chat messages for context)
- **User input piped**: Yes (your query is passed to the tool)
- **Output piped to chat**: Yes (tool output is returned as the assistant's reply)
- **Timeout**: 30 seconds

## Requirements

- [Cha](https://github.com/MehmetMHY/cha/)
- Python 3.7+
- `requests` library (for HTTP requests):  
  Install via
  ```shell
  pip install requests
  ```
- [Cha](https://github.com/MehmetMHY/cha/) installed and configured

**Note:**

If the user does not provide a weather question, the tool will attempt to infer the user's intent from the two most recent chat messages.
