"""Example data for the FESOM model."""

import tarfile
from pathlib import Path

import pytest
import requests

URL = "https://nextcloud.awi.de/s/swqyFgbL2jjgjRo/download/pi_uxarray.tar"
"""str : URL to download the example data from."""


@pytest.fixture(scope="session", autouse=True)
def pi_uxarray_download_data(tmp_path_factory):
    cache_dir = tmp_path_factory.getbasetemp() / "cached_data_pi"
    cache_dir.mkdir(exist_ok=True)
    data_path = cache_dir / "pi_uxarray.tar"

    if not data_path.exists():
        response = requests.get(URL)
        response.raise_for_status()
        with open(data_path, "wb") as f:
            f.write(response.content)
        print(f"Data downloaded: {data_path}.")
    else:
        print(f"Using cached data: {data_path}.")

    return data_path


@pytest.fixture(scope="session", autouse=True)
def pi_uxarray_data(pi_uxarray_download_data):

    data_dir = Path(pi_uxarray_download_data).parent
    with tarfile.open(pi_uxarray_download_data, "r") as tar:
        tar.extractall(data_dir)

    return data_dir / "pi_uxarray"
