import os

from tests.utils.constants import TEST_ROOT

pytest_plugins = [
    "tests.fixtures.CMIP_Tables_Dir",
    "tests.fixtures.CV_Dir",
    "tests.fixtures.config_files",
    "tests.fixtures.configs",
    "tests.fixtures.datasets",
    "tests.fixtures.environment",
    "tests.fixtures.fake_filesystem",
    "tests.fixtures.sample_rules",
]


def pytest_unconfigure(config):

    # Remove all json files
    for file in os.listdir():
        if "pipeline" in file and file.endswith(".json"):
            os.remove(file)
