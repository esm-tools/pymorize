import pathlib

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher


@pytest.fixture
def mini_fs():
    with Patcher() as patcher:
        patcher.fs.create_file("/path/to/test1.txt")
        patcher.fs.create_file("/path/to/test2.txt")
        patcher.fs.create_file("/path/to/test3.txt")
        yield patcher


def test_example_with_pathlib(mini_fs):
    f1 = pathlib.Path("/path/to/test1.txt")
    f2 = pathlib.Path("/path/to/test2.txt")
    f3 = pathlib.Path("/path/to/test3.txt")

    assert f1.exists()
    assert f2.exists()
    assert f3.exists()

    # List the files:
    files = list(pathlib.Path("/path/to").glob("*.txt"))

    assert set(files) == set([f2, f1, f3])
