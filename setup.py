from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.4.7",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI chat tool to easily interface with OpenAI's LLM models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.37.0",
        "groq==0.9.0",
        "tiktoken==0.7.0",
        "beautifulsoup4==4.12.3",
        "selenium==4.23.1",
        "webdriver-manager==4.0.1",
        "yt-dlp==2024.7.16",
        "PyMuPDF==1.24.8",
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
