"""Example data for the FESOM model."""

import pytest

from .shared_cache import download_file, extract_tarfile

URL = "https://nextcloud.awi.de/s/swqyFgbL2jjgjRo/download/pi_uxarray.tar"
"""str : URL to download the example data from."""

MESH_URL = "https://nextcloud.awi.de/s/FCPZmBJGeGaji4y/download/pi_mesh.tgz"
"""str : URL to download the mesh data from."""


@pytest.fixture(scope="session")
def pi_uxarray_download_data():
    # Use shared cache instead of tmp_path_factory
    return download_file(URL, "pi_uxarray.tar")


@pytest.fixture(scope="session")
def pi_uxarray_data(pi_uxarray_download_data):
    # Extract to shared location
    data_dir = extract_tarfile(pi_uxarray_download_data, subfolder="pi_uxarray")
    return data_dir


@pytest.fixture(scope="session")
def pi_uxarray_download_mesh():
    # Use shared cache instead of tmp_path_factory
    return download_file(MESH_URL, "pi_mesh.tgz")


@pytest.fixture(scope="session")
def pi_uxarray_mesh(pi_uxarray_download_mesh):
    # Extract to shared location
    data_dir = extract_tarfile(pi_uxarray_download_mesh, subfolder="pi")
    return data_dir
