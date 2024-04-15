from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.3.1",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI chat tool to easily interface with OpenAI's LLM models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.18.0",
        "tiktoken==0.6.0",
        "beautifulsoup4==4.12.3",
        "selenium==4.19.0",
        "webdriver-manager==4.0.1",
        "yt-dlp==2024.4.9",
        # NOTE: (3-13-2024) this package did not have a PyPi page, so it was forked and git was used instead of PyPi
        "climage @ git+https://github.com/MehmetMHY/CLImage.git#egg=climage",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "cha = cha.main:cli",
        ],
    },
)
