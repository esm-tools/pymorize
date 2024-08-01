import os


def pytest_unconfigure(config):

    # Remove all json files
    for file in os.listdir():
        if "pipeline" in file and file.endswith(".json"):
            os.remove(file)
