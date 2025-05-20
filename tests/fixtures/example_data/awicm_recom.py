"""Example data for the FESOM model."""

import os

import pytest

from .shared_cache import download_file, extract_tarfile

URL = "https://nextcloud.awi.de/s/DaQjtTS9xB7o7pL/download/awicm_1p0_recom.tar"
"""str : URL to download the example data from."""


@pytest.fixture(scope="session")
def awicm_1p0_recom_download_data():
    # Use shared cache instead of tmp_path_factory
    return download_file(URL, "awicm_1p0_recom.tar")


@pytest.fixture(scope="session")
def awicm_1p0_recom_data(awicm_1p0_recom_download_data):
    # Extract to shared location
    data_dir = extract_tarfile(awicm_1p0_recom_download_data)

    # Debug logging
    for root, dirs, files in os.walk(data_dir):
        print(f"Root: {root}")
        for file in files:
            print(f"File: {os.path.join(root, file)}")

    print(f">>> RETURNING: {data_dir / 'awicm_1p0_recom' }")
    return data_dir / "awicm_1p0_recom"
