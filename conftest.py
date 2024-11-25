import os
import re
from pathlib import Path

import pytest

from tests.utils.constants import TEST_ROOT

pytest_plugins = [
    "tests.fixtures.CMIP_Tables_Dir",
    "tests.fixtures.CV_Dir",
    "tests.fixtures.config_files",
    "tests.fixtures.configs",
    "tests.fixtures.environment",
    "tests.fixtures.example_data.fesom_2p6_pimesh",
    "tests.fixtures.example_data.pi_uxarray",
    "tests.fixtures.fake_data.fesom_mesh",
    "tests.fixtures.fake_data.awicm_recom",
    "tests.fixtures.fake_filesystem",
    "tests.fixtures.sample_rules",
]


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.fspath and item.fspath.ext == ".py":
            item.add_marker(pytest.mark.doctest)


@pytest.fixture(autouse=True)
def pathlib_doctest_directive(doctest_namespace):
    """Replace PosixPath/WindowsPath with Path in doc-test output."""
    doctest_namespace["Path"] = Path

    def path_replace(output):
        """Replace platform-specific Path output with generic Path in doc-tests."""
        return re.sub(r"(PosixPath|WindowsPath)\((.*?)\)", r"Path(\2)", output)

    doctest_namespace["path_replace"] = path_replace


def pytest_unconfigure(config):
    """Remove all JSON files containing 'pipeline' in their name."""
    for file in os.listdir():
        if "pipeline" in file and file.endswith(".json"):
            os.remove(file)
