from setuptools import setup, find_packages

setup(
    name='cha',
    version='0.1.0',
    packages=find_packages(),
    license='MIT',
    description='A simple CLI tool to chat with certain LLM models',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=[
        'openai==0.28.0',
        'requests==2.31.0'
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'cha = cha.main:cli',
        ],
    },
)
