# Development Tools Overview

## About

The tools in this directory help with Cha development, testing, and maintenance. These utilities provide essential functionality for developers working on the Cha project.

## Files

- **checkup.py**: Verifies that all external resources used by Cha are set up correctly. This comprehensive script checks dependencies, API keys, and system requirements. While some issues may not prevent Cha from working, this script serves as a thorough checker to identify missing or failing components.

- **toolkit.py**: A versatile utility for project analysis. It includes functions for:

  - Counting lines of code by file extension.
  - Measuring startup time performance.
  - Listing project dependencies.
  - Displaying Git repository statistics.
  - Comparing installation sizes and startup times between [cha](https://github.com/MehmetMHY/cha/) and [ch](https://github.com/MehmetMHY/ch).

- **update.py**: Automates updating the package version in `setup.py` and assists with version management during development. Simplifies the process of bumping version numbers for releases.
