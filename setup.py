import io
import os
import re

import versioneer
from setuptools import find_packages, setup


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type("")
    with io.open(filename, mode="r", encoding="utf-8") as fd:
        return re.sub(text_type(r":[a-z]+:`~?(.*?)`"), text_type(r"``\1``"), fd.read())


setup(
    name="pymorize",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    url="https://github.com/pgierz/pymorize",
    license="MIT",
    author="Paul Gierz",
    author_email="pgierz@awi.de",
    description="Makes CMOR Simple",
    long_description=read("README.rst"),
    package_dir={"": "src"},
    packages=find_packages(where="src", exclude=("tests",)),
    install_requires=[
        "rich-click",
        "click-loguru",
        "xarray",
        "versioneer",
    ],
    entry_points={
        "console_scripts": [
            "pymorize=pymorize.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
