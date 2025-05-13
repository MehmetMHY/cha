# Cha & SearXNG

## About

SearXNG is an open-source search engine. The catch with it is that you have to host it. This is easy to do with Docker and the scripts located in this directory but it's not as convenient as using DuckDuckGo's free API. But, DuckDuckGo's free API is limited and you can run into rate limit issues with enough use. Also, using search API(s) can be difficult to setup and you have to manage another API key. Due to this, setting up SearXNG is not required to use Cha but it is heavily recommended you utilize SearXNG.

For more information, visit the [SearXNG documentation](https://docs.searxng.org/).

## How To Setup

1. Make sure to install and setup [Docker](https://www.docker.com/)

2. Run the setup script and follow each instruction: `bash ./setup.sh`

3. Try it out by running the example script ([Python](https://www.python.org/)): `python3 ./example.py`
