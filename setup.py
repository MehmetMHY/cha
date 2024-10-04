from setuptools import setup, find_packages

setup(
    name="cha",
    version="0.6.1",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI chat tool for easy interaction with OpenAI's LLM models and other platforms",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "openai==1.43.0",
        "anthropic==0.34.2",
        "groq==0.11.0",
        "beautifulsoup4==4.12.3",
        "selenium==4.24.0",
        "webdriver-manager==4.0.2",
        "yt-dlp==2024.8.6",
        "PyMuPDF==1.24.10",
        # NOTE: (3-13-2024) Using Git because PyPi page does not exist
        "climage @ git+https://github.com/MehmetMHY/CLImage.git#egg=climage",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "cha = cha.main:cli",
            "cla = cha.cla:cli",
            "grq = cha.grq:cli",
        ],
    },
)
