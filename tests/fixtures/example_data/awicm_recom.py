"""Example data for the FESOM model."""

# import os
import shutil
import tarfile
from pathlib import Path

import pytest
import requests

URL = "https://nextcloud.awi.de/s/AL2cFQx5xGE473S/download/awicm-1p0-recom.tar"
"""str : URL to download the example data from."""


@pytest.fixture(scope="session")
def awicm_1p0_recom_download_data(tmp_path_factory):
    cache_dir = tmp_path_factory.getbasetemp() / "cached_data"
    cache_dir.mkdir(exist_ok=True)
    data_path = cache_dir / "awicm_1p0_recom.tar"

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
def awicm_1p0_recom_data(awicm_1p0_recom_download_data):
    I_need_to_make_a_local_copy = True
    # Check if you have a local copy
    # Useful for testing on your local laptop
    local_cache_path = Path(
        "~/.cache/pytest/github.com/esm-tools/pymorize"
    ).expanduser()
    local_cache_path = local_cache_path / "awicm_1p0_recom"
    if local_cache_path.exists():
        I_need_to_make_a_local_copy = False
        print(f"Using local cache: {local_cache_path}")
        return local_cache_path
    data_dir = Path(awicm_1p0_recom_download_data).parent / "awicm_1p0_recom"
    if not data_dir.exists():
        with tarfile.open(awicm_1p0_recom_download_data, "r") as tar:
            tar.extractall(data_dir)
        print(f"Data extracted to: {data_dir}.")
    else:
        print(f"Using cached extraction: {data_dir}.")

    # for root, dirs, files in os.walk(data_dir):
    #     print(f"Root: {root}")
    #     for file in files:
    #         print(f"File: {os.path.join(root, file)}")

    # print(f">>> RETURNING: {data_dir / 'awicm_1p0_recom' }")
    if I_need_to_make_a_local_copy:
        local_cache_path.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copytree(
                data_dir / "awicm_1p0_recom",
                local_cache_path,
                dirs_exist_ok=True,
                ignore_dangling_symlinks=True,
            )
            # (data_dir / "awicm_1p0_recom").copy(local_cache_path, follow_symlinks=True)
            print(f"Local cache created: {local_cache_path}")
        except Exception as e:
            print(f"Failed to create local cache: {e}")
            # Remove the local cache
            shutil.rmtree(local_cache_path)
    print(f">>> RETURNING: {data_dir / 'awicm_1p0_recom' }")
    return data_dir / "awicm_1p0_recom"
