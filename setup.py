"""A setuptools based setup module."""
from os import path
from setuptools import setup, find_packages
from io import open

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
     name='discord-trivia-bot',
     version='0.0.1',
     description='discord bot for trivia',
     long_description=long_description,
     long_description_content_type='text/markdown',
     url='https://github.com/themarathoncontinues/discord-trivia-bot',
     author='Leon Kozlowski, Jeremy Hikind',
     author_email='leonkozlowski@gmail.com',
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     python_requires='>=3.6',
     keywords='discord bot trivia',
     packages=find_packages(),
     install_requires=[
         'requests',
         'discord',
         'python-dotenv'
     ]
)