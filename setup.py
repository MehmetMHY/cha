from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.8.1",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI chat tool for easy interaction with OpenAI's LLM models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.52.0",
        "anthropic==0.37.0",
        "beautifulsoup4==4.12.3",
        "yt-dlp==2024.10.22",
        "youtube-transcript-api==0.6.2",
        "PyMuPDF==1.24.12",
        "pillow==11.0.0",
        "tiktoken==0.8.0",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": ["cha = cha.main:cli", "cla = cha.cla:cli"],
    },
)
