from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.13.0",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI tool for chatting, web scraping, and image generation with OpenAI's models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.63.2",
        "beautifulsoup4==4.13.3",
        "yt-dlp==2025.2.19",
        "youtube-transcript-api==0.6.3",
        "PyMuPDF==1.25.3",
        "pillow==11.1.0",
        "tiktoken==0.9.0",
        "duckduckgo_search==7.4.2",
        "pdf2image==1.17.0",
        "python-docx==1.1.2",
        "openpyxl==3.1.5",
        "chardet==5.2.0",
        "pathspec==0.12.1",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": ["cha = cha.main:cli"],
    },
)
