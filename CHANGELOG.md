# Changelog

## Version 0.7.0

### Massive refactor, optimization, and bug fixes

- Commit: [`b66b0632`](https://github.com/MehmetMHY/cha/tree/b66b0632af1447e699e76758729579fcd646d7ca)
- Previous Commit: [`6b2f6b3b`](https://github.com/MehmetMHY/cha/tree/6b2f6b3b90cb8c061e48e8a59cc59619946f4353)

### Additional Notes

- Removed `grq` and all Groq-based API calls
- Remove Selenium scraper
- Updated YouTube scraper to include video's metadata
- Speed up and improved YouTube scraper transcript scraper though the `youtube-transcript-api` package
- Completely refactored Cla, making it cleaner and more simple
- Updated Cla to support scraping though Cha's scrapers
- Included metadata in generated images and added a CLI option to view an image's metadata
- Modified argument handling logic, eliminating the need for `cha.sh`
- Simplified and cleaned printing, making the code simpler and smaller. Also made prints look nicer
- Removed Climage because it did not provide any value even though it's really cool
- Most websites can be scraped using `requests.get()`, which is lighter and faster, so Selenium was removed

## Version 0.6.0

### Removed Answer-Search

- Commit: [`632a402c`](https://github.com/MehmetMHY/cha/tree/632a402c82b053d7321d90d26ccf850cf81f75c0)
- Previous Commit: [`126b3148`](https://github.com/MehmetMHY/cha/tree/126b314812ed0e4eb76f44c38dadc01492d07a5f)

### Additional Notes

- Removed Brave API integration

## Version 0.3.3

### Removed OpenAI cost estimator logic

- Commit: [`1ff945e1`](https://github.com/MehmetMHY/cha/tree/1ff945e1ca21851a8d12aa5c1ebd2bc19b781d6f)
- Previous Commit: [`aa1bc51a`](https://github.com/MehmetMHY/cha/tree/aa1bc51ace9006d138fde9c032c63c50d48435ff)

## Version 0.2.5

### Added Answer-Search feature

- Commit: [`6a35c904`](https://github.com/MehmetMHY/cha/tree/6a35c904335fa11690d2c0a1b07f5a30871de4b5)
- Previous Commit: [`5b524768`](https://github.com/MehmetMHY/cha/tree/5b524768eb8de316e0f146d688a954f9fbfc832d)

### Additional Notes

- Added Answer-Search feature which is based off of [Perplexity](https://www.perplexity.ai/)
- Added [Brave API](https://brave.com/search/api/) to the code base
- Brave does not have an official Python SDK so I had to make my own function

## Version 0.1.0

### Migrated project to act like a Python package (pip)

- Commit: [`78f51f78`](https://github.com/MehmetMHY/cha/tree/78f51f78e83aad69e319b6206fe6c0ba85d7f3c7)
- Previous Commit: [`8e1102e6`](https://github.com/MehmetMHY/cha/tree/8e1102e681ec942572308d38d49a53a123e9f29e)

### Removed Together.AI support

- Commit: [`94b1b7da`](https://github.com/MehmetMHY/cha/tree/94b1b7da85bed78bffe07a234c5e240f8cc64891)
- Previous Commit: [`0554d4c5`](https://github.com/MehmetMHY/cha/tree/0554d4c5a4dd46d7d05ef44675cf1e81df65962a)

### Removed Ollama CLI wrapper

- Commit: [`8e1102e6`](https://github.com/MehmetMHY/cha/tree/8e1102e681ec942572308d38d49a53a123e9f29e)
- Previous Commit: [`6f558854`](https://github.com/MehmetMHY/cha/tree/6f5588541924bb7e1b4c68b0784e036b648c5b38)

### Removed LLM_WEBSITES open feature

- Commit: [`7c82c927`](https://github.com/MehmetMHY/cha/tree/7c82c927d5f5b3ec89ebb2b6ecf4785b2649d322)
- Previous Commit: [`080b885a`](https://github.com/MehmetMHY/cha/tree/080b885aad724e910b28cc94d8c5b6786afd0746)

## Version 0.0.0

### Initial non-pip project state

- Commit: [`8e1102e6`](https://github.com/MehmetMHY/cha/tree/8e1102e681ec942572308d38d49a53a123e9f29e)
