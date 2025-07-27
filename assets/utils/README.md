# Utils Overview

## About

The tools in this directory primarily help to test Cha during development and provide utilities for development maintenance. These tools work together to give you quick insight into Cha's development state, ensuring smooth and efficient monitoring and testing.

## Files

- **checkup.py**: Verifies that all external resources used by Cha are set up correctly. While some issues may not prevent Cha from working, this script serves as a thorough checker to identify missing or failing components.

- **lines.py**: Counts lines of code by file extension in a given directory, ignoring files and folders specified in `.gitignore`. Useful for understanding project size and composition.

- **startup.py**: Measures the startup time of the `cha` command or any specified shell command to help benchmark and optimize performance.

- **update.py**: Automates updating the package version in `setup.py` and checks for dependency updates, simplifying maintenance during development.
