# Development Tools Overview

## About

The tools in this directory help with Cha development, testing, and maintenance. These utilities provide essential functionality for developers working on the Cha project.

## Files

- **checkup.py**: Verifies that all external resources used by Cha are set up correctly. This comprehensive script checks dependencies, API keys, and system requirements. While some issues may not prevent Cha from working, this script serves as a thorough checker to identify missing or failing components.

- **toolkit.py**: Contains utility functions for measuring startup time and performance benchmarking. Provides tools to measure how long the `cha` command or other shell commands take to initialize, helping with performance optimization.

- **update.py**: Automates updating the package version in `setup.py` and assists with version management during development. Simplifies the process of bumping version numbers for releases.
