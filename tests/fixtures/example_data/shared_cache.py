"""Shared cache implementation for example data."""

import os
import tarfile
from pathlib import Path

import requests


def get_shared_cache_dir():
    """
    Get the shared cache directory for all test sessions.

    This creates a persistent cache directory that can be shared across
    all test sessions, avoiding redundant downloads.

    Returns:
        Path: Path to the shared cache directory
    """
    # Use a persistent location that doesn't change between test sessions
    # First try to use a directory in the user's home
    home_cache = Path.home() / ".cache" / "pymor-test-data"

    # If we can't write to home directory, fall back to /tmp/pymor-test-data
    if os.access(Path.home(), os.W_OK):
        cache_dir = home_cache
    else:
        cache_dir = Path("/tmp/pymor-test-data")

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def download_file(url, filename, cache_dir=None):
    """
    Download a file if it doesn't exist in the cache.

    Args:
        url (str): URL to download the file from
        filename (str): Name to save the file as
        cache_dir (Path, optional): Directory to save the file in.
                                   Defaults to shared cache dir.

    Returns:
        Path: Path to the downloaded file
    """
    if cache_dir is None:
        cache_dir = get_shared_cache_dir()

    file_path = cache_dir / filename

    if not file_path.exists():
        print(f"Downloading {url} to {file_path}...")
        response = requests.get(url)
        response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Data downloaded: {file_path}.")
    else:
        print(f"Using shared cached data: {file_path}.")

    return file_path


def extract_tarfile(tar_path, extract_dir=None, subfolder=None):
    """
    Extract a tarfile to a directory if it doesn't exist.

    Args:
        tar_path (Path): Path to the tarfile
        extract_dir (Path, optional): Directory to extract to.
                                     Defaults to parent of tar_path.
        subfolder (str, optional): Subfolder within the tarfile to return.
                                  Defaults to None.

    Returns:
        Path: Path to the extracted directory
    """
    if extract_dir is None:
        extract_dir = tar_path.parent

    # Determine the extraction target directory
    if subfolder:
        target_dir = extract_dir / subfolder
    else:
        # Use the tar filename without extension as the target directory
        target_dir = extract_dir / tar_path.stem

    if not target_dir.exists():
        print(f"Extracting {tar_path} to {target_dir}...")
        with tarfile.open(tar_path, "r") as tar:
            tar.extractall(extract_dir)
        print(f"Data extracted to: {target_dir}.")
    else:
        print(f"Using shared extracted data: {target_dir}.")

    return target_dir
