import os
import pathlib
import re
from pathlib import Path
from unittest import mock

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher
from pyfakefs.fake_pathlib import FakePath

from pymorize.gather_inputs import (_input_pattern_from_env, files_to_string,
                                    input_files_in_path, resolve_symlinks,
                                    sort_by_year,
                                    validate_rule_has_marked_regex)

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
def config(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def config_bare():
    return {"pymorize": {}}


@pytest.fixture
def config_only_env_name():
    return {
        "pymorize": {
            "pattern_env_var_name": "CMOR_PATTERN",
        }
    }


@pytest.fixture
def config_only_env_value():
    return {
        "pymorize": {
            "pattern_env_var_value": "test.*nc",
        }
    }


@pytest.fixture
def config_both():
    return {
        "pymorize": {
            "pattern_env_var_name": "CMOR_PATTERN",
            "pattern_env_var_value": "other_test.*nc",
        }
    }


@pytest.fixture
def fake_filesystem():
    with Patcher() as patcher:
        patcher.fs.create_file("/path/to/test1.txt")
        patcher.fs.create_file("/path/to/test2.txt")
        patcher.fs.create_file("/path/to/fesom_test.nc")
        patcher.fs.create_file("/path/to/other_test123.nc")
        patcher.fs.create_file("/path/to/test.nc")
        yield patcher


@pytest.fixture
def fake_filesystem_with_symlinks():
    with Patcher() as patcher:
        # Create some fake files and a symlink
        patcher.fs.create_file("/path/to/file1")
        patcher.fs.create_file("/path/to/file2")
        patcher.fs.create_file("/path/to/actual/file")
        patcher.fs.create_symlink("/path/to/symlink", "/path/to/actual/file")

        yield patcher


@pytest.fixture
def clean_environment():
    with mock.patch.dict(os.environ, {}, clear=True):
        yield


@pytest.mark.parametrize(
    "config, expected_pattern, expected_output",
    [
        (
            "config_bare",  # Matches any input
            re.compile(".*"),
            [
                pathlib.Path("/path/to/test1.txt"),
                pathlib.Path("/path/to/test2.txt"),
                pathlib.Path("/path/to/fesom_test.nc"),
                pathlib.Path("/path/to/other_test123.nc"),
                pathlib.Path("/path/to/test.nc"),
            ],
        ),
        (
            "config_only_env_name",
            re.compile(".*"),
            [
                pathlib.Path("/path/to/test1.txt"),
                pathlib.Path("/path/to/test2.txt"),
                pathlib.Path("/path/to/fesom_test.nc"),
                pathlib.Path("/path/to/other_test123.nc"),
                pathlib.Path("/path/to/test.nc"),
            ],
        ),
        (
            "config_only_env_value",
            re.compile("test.*nc"),
            [pathlib.Path("/path/to/test.nc")],
        ),
        (
            "config_both",
            re.compile("other_test.*nc"),
            [pathlib.Path("/path/to/other_test123.nc")],
        ),
    ],
    indirect=[  # This tells pytest to treat 'config' as a fixture
        "config",
    ],
)
def test_listing_function(config, expected_pattern, expected_output, fake_filesystem):
    pattern = _input_pattern_from_env(config)
    assert pattern == expected_pattern
    output = input_files_in_path("/path/to", pattern)
    assert set(expected_output) == set(output)


def test_default_pattern(config_bare, clean_environment):
    pattern = _input_pattern_from_env(config_bare)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test")


def test_custom_pattern_name(config_only_env_name, clean_environment):
    os.environ["CMOR_PATTERN"] = "test.*"
    pattern = _input_pattern_from_env(config_only_env_name)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test123")
    assert not pattern.match("123test")


def test_custom_pattern_value(config_only_env_value, clean_environment):
    pattern = _input_pattern_from_env(config_only_env_value)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test1.nc")
    assert pattern.match("test.nc")
    assert not pattern.match("something_test.nc")


def test_custom_both(config_both, clean_environment):
    pattern = _input_pattern_from_env(config_both)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("other_test123.nc")
    os.environ["CMOR_PATTERN"] = "test.*"
    pattern = _input_pattern_from_env(config_both)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test123")
    assert not pattern.match("123test")


def test_env_var_no_match(config_only_env_name, fake_filesystem, clean_environment):
    os.environ["CMOR_PATTERN"] = "no_match*"
    pattern = _input_pattern_from_env(config_only_env_name)
    output = input_files_in_path("/path/to", pattern)
    assert output == []


def test_env_var_partial_match(
    config_only_env_name, fake_filesystem, clean_environment
):
    os.environ["CMOR_PATTERN"] = "test1.*"
    pattern = _input_pattern_from_env(config_only_env_name)
    output = input_files_in_path("/path/to", pattern)
    assert output == [pathlib.Path("/path/to/test1.txt")]


def test_nonexistent_path(config_bare, fake_filesystem, clean_environment):
    pattern = _input_pattern_from_env(config_bare)
    with pytest.raises(FileNotFoundError):
        input_files_in_path("/nonexistent/path", pattern)


def test_empty_directory(config_bare, fake_filesystem, clean_environment):
    fake_filesystem.fs.create_dir("/empty/path")
    pattern = _input_pattern_from_env(config_bare)
    output = input_files_in_path("/empty/path", pattern)
    assert output == []


@pytest.mark.xfail(reason="subdirectories are not supported")
def test_subdirectories_should_fail(config_bare, fake_filesystem, clean_environment):
    fake_filesystem.fs.create_file("/path/to/subdir/test3.txt")
    pattern = _input_pattern_from_env(config_bare)
    output = input_files_in_path("/path/to", pattern)
    assert output == [
        pathlib.Path("/path/to/test1.txt"),
        pathlib.Path("/path/to/test2.txt"),
        pathlib.Path("/path/to/fesom_test.nc"),
        pathlib.Path("/path/to/other_test123.nc"),
        pathlib.Path("/path/to/subdir/test3.txt"),
    ]


def test_resolve_symlinks(fake_filesystem_with_symlinks):
    files = [Path("/path/to/file1"), Path("/path/to/symlink")]
    resolved_files = resolve_symlinks(files)
    assert resolved_files == [Path("/path/to/file1"), Path("/path/to/actual/file")]


def test_resolve_symlinks_raises_type_error():
    with pytest.raises(TypeError):
        resolve_symlinks(["not", "paths"])


@pytest.fixture
def fake_filesystem_with_datestamps_years():
    with Patcher() as patcher:
        fpattern = re.compile(r".*(?P<year>\d{4}).*")
        files = [
            pathlib.Path(f"/path/to/file_{year}.txt") for year in range(2000, 2010)
        ]
        for file in files:
            patcher.fs.create_file(file)
        yield patcher


def test_sort_by_year(fake_filesystem_with_datestamps_years):
    # Arrange
    files = [Path(f"/path/to/file_{year}.txt") for year in range(2000, 2010)]
    # Shuffle the list of files
    import random

    random.shuffle(files)
    fpattern = re.compile(r".*(?P<year>\d{4}).*")

    # Act
    sorted_files = sort_by_year(files, fpattern)

    # Assert
    assert sorted_files == [
        Path(f"/path/to/file_{year}.txt") for year in range(2000, 2010)
    ]


def test_files_to_string():
    # Arrange
    files = [pathlib.Path("path/to/file1"), pathlib.Path("path/to/file2")]
    expected_output = "path/to/file1,path/to/file2"

    # Act
    output = files_to_string(files)

    # Assert
    assert output == expected_output


def test_files_to_string_with_custom_separator():
    # Arrange
    files = [pathlib.Path("path/to/file1"), pathlib.Path("path/to/file2")]
    expected_output = "path/to/file1 - path/to/file2"
    separator = " - "

    # Act
    output = files_to_string(files, separator)

    # Assert
    assert output == expected_output


def test_validate_rule_has_marked_regex_with_required_mark():
    rule = {"pattern": "test(?P<year>[0-9]{4})"}
    assert validate_rule_has_marked_regex(rule) == True


def test_validate_rule_has_marked_regex_without_required_mark():
    rule = {"pattern": "test"}
    assert validate_rule_has_marked_regex(rule) == False


def test_validate_rule_has_marked_regex_with_none_pattern():
    rule = {"pattern": None}
    assert validate_rule_has_marked_regex(rule) == False


def test_validate_rule_has_marked_regex_with_multiple_required_marks():
    rule = {"pattern": "test(?P<year>[0-9]{4})(?P<month>[0-9]{2})"}
    assert validate_rule_has_marked_regex(rule, ["year", "month"]) == True


def test_validate_rule_has_marked_regex_without_all_required_marks():
    rule = {"pattern": "test(?P<year>[0-9]{4})"}
    assert validate_rule_has_marked_regex(rule, ["year", "month"]) == False
