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


docs_require = read("doc/requirements.txt").splitlines()


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
        "cerberus",
        "cf_xarray",
        "cftime",
        "chemicals",
        "click-loguru",
        "dask",
        "dask_jobqueue",
        "deprecation",
        "distributed",
        "dpath",
        "flexparser < 0.4",  # NOTE(PG): See https://tinyurl.com/ypf99xnh
        "flox",
        "imohash",
        "netcdf4",
        "numbagg",
        "pendulum",
        "pint-xarray",
        "prefect[dask]",
        "pyyaml",
        "questionary",
        "randomname",
        "rich-click",
        "streamlit",
        "tqdm",
        "versioneer",
        "xarray",
    ],
    extras_require={
        "dev": [
            "black",
            "dill",
            "flake8",
            "isort",
            "pooch",
            "pre-commit",
            "pyfakefs",
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-xdist",
            "sphinx",
            "sphinx_rtd_theme",
        ],
        "doc": docs_require,
    },
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
