from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.7.1",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI chat tool for easy interaction with OpenAI's LLM models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.51.2",
        "anthropic==0.36.1",
        "beautifulsoup4==4.12.3",
        "yt-dlp==2024.10.7",
        "youtube-transcript-api==0.6.2",
        "PyMuPDF==1.24.11",
        "pillow==10.3.0",
    ],
    python_requires=">=3.9.2",
    entry_points={
        "console_scripts": ["cha = cha.main:cli", "cla = cha.cla:cli"],
    },
)
