"""Example data for the FESOM model."""

import tarfile
from pathlib import Path

import pytest
import requests

URL = "https://nextcloud.awi.de/s/AL2cFQx5xGE473S/download/fesom_2p6_pimesh.tar"
"""str : URL to download the example data from."""


@pytest.fixture(scope="session")
def fesom_2p6_esm_tools_download_data(tmp_path_factory):
    cache_dir = tmp_path_factory.getbasetemp() / "cached_data"
    cache_dir.mkdir(exist_ok=True)
    data_path = cache_dir / "fesom_2p6_pimesh.tar.gz"

    if not data_path.exists():
        response = requests.get(URL)
        response.raise_for_status()
        with open(data_path, "wb") as f:
            f.write(response.content)
        print(f"Data downloaded: {data_path}.")
    else:
        print(f"Using cached data: {data_path}.")

    return data_path


@pytest.fixture(scope="session")
def fesom_2p6_pimesh_esm_tools_data(fesom_2p6_esm_tools_download_data):
    data_dir = Path(fesom_2p6_esm_tools_download_data).parent
    if not data_dir.exists():
        with tarfile.open(fesom_2p6_esm_tools_download_data, "r") as tar:
            tar.extractall(data_dir)
        print(f"Data extracted to: {data_dir}.")
    else:
        print(f"Using cached extraction: {data_dir}.")

    return data_dir / "fesom_2p6_pimesh"
