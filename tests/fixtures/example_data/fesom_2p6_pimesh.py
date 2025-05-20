"""Example data for the FESOM model."""

import shutil
from pathlib import Path

import pytest

from .shared_cache import download_file, extract_tarfile

URL = "https://nextcloud.awi.de/s/AL2cFQx5xGE473S/download/fesom_2p6_pimesh.tar"
"""str : URL to download the example data from."""


@pytest.fixture(scope="session")
def fesom_2p6_esm_tools_download_data():
    # Use shared cache instead of tmp_path_factory
    return download_file(URL, "fesom_2p6_pimesh.tar")


@pytest.fixture(scope="session")
def fesom_2p6_pimesh_esm_tools_data(fesom_2p6_esm_tools_download_data):
    # Check if we have a local copy in the user's home directory
    # This is useful for testing on a local laptop
    local_cache_path = (
        Path("~/.cache/pytest/github.com/esm-tools/pymor").expanduser()
        / "fesom_2p6_pimesh"
    )
    if local_cache_path.exists():
        print(f"Using local cache: {local_cache_path}")
        return local_cache_path

    # Extract to shared location
    data_dir = extract_tarfile(fesom_2p6_esm_tools_download_data)

    # Try to create a local copy for faster access in future runs
    try:
        local_cache_path.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            data_dir / "fesom_2p6_pimesh",
            local_cache_path,
            dirs_exist_ok=True,
            ignore_dangling_symlinks=True,
        )
        print(f"Local cache created: {local_cache_path}")
    except Exception as e:
        print(f"Failed to create local cache: {e}")
        # Remove the local cache if it failed
        if local_cache_path.exists():
            shutil.rmtree(local_cache_path)

    print(f">>> RETURNING: {data_dir / 'fesom_2p6_pimesh' }")
    return data_dir / "fesom_2p6_pimesh"
