from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.10.11",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI tool for chatting, web scraping, and image generation with OpenAI's models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.57.4",
        "beautifulsoup4==4.12.3",
        "yt-dlp==2024.12.13",
        "youtube-transcript-api==0.6.3",
        "PyMuPDF==1.25.1",
        "pillow==11.0.0",
        "tiktoken==0.8.0",
        "duckduckgo_search==6.4.1",
        "pdf2image==1.17.0",
        "python-docx==1.1.2",
        "openpyxl==3.1.5",
        "chardet==5.2.0",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": ["cha = cha.main:cli"],
    },
)
