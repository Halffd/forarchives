from setuptools import setup, find_packages

setup(
    name="forarchives-search",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'pandas',
        'requests',
        'beautifulsoup4',
        'tornado'
    ],
) 