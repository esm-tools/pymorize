import io
import os
import re

from setuptools import find_packages, setup

import versioneer


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type("")
    with io.open(filename, mode="r", encoding="utf-8") as fd:
        return re.sub(text_type(r":[a-z]+:`~?(.*?)`"), text_type(r"``\1``"), fd.read())


setup(
    name="pymorize",
    python_requires=">=3.9, <4",
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
        "cf_xarray",
        "chemicals",
        "click-loguru",
        "dill",
        "dpath",
        "pendulum",
        "pint-xarray",
        "pyyaml",
        "questionary",
        "rich-click",
        "versioneer",
        "xarray",
    ],
    development_requires=[
        "black",
        "flake8",
        "isort",
        "pre-commit",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-xdist",
        "sphinx",
        "sphinx_rtd_theme",
    ],
    entry_points={
        "console_scripts": [
            "pymorize=pymorize.cli:main",
        ],
        "pymorize.cli_subcommands": [
            "plugins=pymorize.plugins:plugins",
            "externals=pymorize.externals:externals",
        ],
    },
    package_data={},
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
