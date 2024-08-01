import os

pytest_plugins = [
    "tests.fixtures.configs",
    "tests.fixtures.environment",
    "tests.fixtures.fake_filesystem",
]


def pytest_unconfigure(config):

    # Remove all json files
    for file in os.listdir():
        if "pipeline" in file and file.endswith(".json"):
            os.remove(file)
