from pathlib import Path

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher
from pyfakefs.fake_pathlib import FakePath

# monkeypatch Path.__eq__ so that pyfakefs FakePaths compare equal to real pathlib.Paths
#
# Path somehow gets monkeypatched during testing, so in order to have access
# to the original class we'll simply create an instance of it
PATH = object.__new__(Path)


def path_eq(self, other):
    Path = type(PATH)

    if isinstance(other, (Path, FakePath)):
        return str(self) == str(other)

    return super(Path, self).__eq__(other)


Path.__eq__ = path_eq


@pytest.fixture
def fs(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def fs_with_datestamps_years():
    with Patcher() as patcher:
        # fpattern = re.compile(r".*(?P<year>\d{4}).*")
        files = [Path(f"/path/to/file_{year}.txt") for year in range(2000, 2010)]
        for file in files:
            patcher.fs.create_file(file)
        yield patcher


@pytest.fixture
def fs_basic():
    with Patcher() as patcher:
        patcher.fs.create_file("/path/to/test1.txt")
        patcher.fs.create_file("/path/to/test2.txt")
        patcher.fs.create_file("/path/to/fesom_test.nc")
        patcher.fs.create_file("/path/to/other_test123.nc")
        patcher.fs.create_file("/path/to/test.nc")
        yield patcher


@pytest.fixture
def fs_with_symlinks():
    with Patcher() as patcher:
        # Create some fake files and a symlink
        patcher.fs.create_file("/path/to/file1")
        patcher.fs.create_file("/path/to/file2")
        patcher.fs.create_file("/path/to/actual/file")
        patcher.fs.create_symlink("/path/to/symlink", "/path/to/actual/file")

        yield patcher


@pytest.fixture
def fs_with_subdirs():
    with Patcher() as patcher:
        patcher.fs.create_file("/path/to/test1.txt")
        patcher.fs.create_file("/path/to/test2.txt")
        patcher.fs.create_file("/path/to/fesom_test.nc")
        patcher.fs.create_file("/path/to/other_test123.nc")
        patcher.fs.create_file("/path/to/subdir/test3.txt")
        yield patcher
