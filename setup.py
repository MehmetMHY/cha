from setuptools import setup, find_packages

setup(
    name='cha',
    version='0.2.0',
    packages=find_packages(),
    license='MIT',
    description="A simple CLI chat tool to easily interface with OpenAI's LLM models",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'openai==0.28.0',
        'beautifulsoup4==4.12.3',
        'selenium==4.18.1',
        'webdriver-manager==4.0.1',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'cha = cha.main:cli',
        ],
    },
)
