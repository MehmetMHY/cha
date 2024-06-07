from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.4.3",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI chat tool to easily interface with OpenAI's LLM models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.32.0",
        "tiktoken==0.7.0",
        "beautifulsoup4==4.12.3",
        "selenium==4.21.0",
        "webdriver-manager==4.0.1",
        "yt-dlp==2024.5.27",
        # NOTE: (3-13-2024) Using Git because PyPi page does not exist
        "climage @ git+https://github.com/MehmetMHY/CLImage.git#egg=climage",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "cha = cha.main:cli",
        ],
    },
)
