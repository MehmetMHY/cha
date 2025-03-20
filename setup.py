from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.15.17",
    packages=find_packages(),
    license="MIT",
    description="A simple cli tool that simplifies interactions with AI models, offering features like chat, web scraping, and answer search. It supports multiple platforms and file types, enhancing productivity for all.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.67.0",
        "beautifulsoup4==4.13.3",
        "yt-dlp==2025.2.19",
        "youtube-transcript-api==1.0.2",
        "PyMuPDF==1.25.4",
        "tiktoken==0.9.0",
        "duckduckgo_search==7.5.2",
        "python-docx==1.1.2",
        "openpyxl==3.1.5",
        "chardet==5.2.0",
        "pathspec==0.12.1",
        "openai-whisper==20240930",
        "moviepy==2.1.2",
        "pillow==10.4.0",
        "pytesseract==0.3.13",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": ["cha = cha.main:cli", "cla = cha.cla:cli"],
    },
)
