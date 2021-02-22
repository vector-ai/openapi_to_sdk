import os
from setuptools import setup, find_packages

name = 'openapi_to_sdk'
version = '0.1.1'

setup(
    name=name,
    version=version,
    author="OnSearch Pty Ltd",
    author_email="dev@vctr.ai",
    description="API to Python SDK",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    keywords="SDK to API Automation.",
    license="Apache",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3",
    #install_requires=['requirements.txt'],
)
