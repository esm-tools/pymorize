import os

from tests.utils.constants import TEST_ROOT

pytest_plugins = [
    "tests.fixtures.configs",
    "tests.fixtures.environment",
    "tests.fixtures.fake_filesystem",
    "tests.fixtures.sample_rules",
    "tests.fixtures.config_files",
    "tests.fixtures.CV_Dir",
    "tests.fixtures.CMIP_Tables_Dir",
]


def pytest_unconfigure(config):

    # Remove all json files
    for file in os.listdir():
        if "pipeline" in file and file.endswith(".json"):
            os.remove(file)
