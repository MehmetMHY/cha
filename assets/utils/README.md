# Utils Overview

## About

The tools in this directory primarily help to test Cha during development, provide an overview of Cha’s usage and performance, and allow you to monitor your usage and costs when local Cha is enabled. These tools work together to give you quick insight into Cha’s development state and usage metrics, ensuring smooth and efficient monitoring and testing.

## Files

- **checkup.py**: Verifies that all external resources used by Cha are set up correctly. While some issues may not prevent Cha from working, this script serves as a thorough checker to identify missing or failing components.

- **costs.json**: Holds pricing information for various AI models across different platforms. This data is used to estimate token costs and billing.

- **quantify.py**: Gathers and displays detailed statistics about your chat history, token usage, chat duration, and estimated expenses based on model costs that are manually defined in `costs.json`.

- **lines.py**: Counts lines of code by file extension in a given directory, ignoring files and folders specified in `.gitignore`. Useful for understanding project size and composition.

- **startup.py**: Measures the startup time of the `cha` command or any specified shell command to help benchmark and optimize performance.

- **update.py**: Automates updating the package version in `setup.py` and checks for dependency updates, simplifying maintenance during development.
