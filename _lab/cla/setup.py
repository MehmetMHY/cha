from setuptools import setup, find_packages

setup(
    name="cla",
    version="0.1.3",
    packages=find_packages(),
    license="MIT",
    description="A simple CLI chat tool to easily interface with Anthropic's LLM models",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "anthropic==0.31.2",
        "beautifulsoup4==4.12.3",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "cla = cla.main:cli",
        ],
    },
)
