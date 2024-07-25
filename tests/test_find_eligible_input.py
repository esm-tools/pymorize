import os
import pathlib
import re
from pathlib import Path
from unittest import mock

import pytest
from pyfakefs.fake_filesystem_unittest import Patcher
from pyfakefs.fake_pathlib import FakePath

from pymorize.gather_inputs import _input_pattern_from_env, input_files_in_path

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
            "pattern_env_var_default": "test*nc",
        }
    }


@pytest.fixture
def config_both():
    return {
        "pymorize": {
            "pattern_env_var_name": "CMOR_PATTERN",
            "pattern_env_var_default": "other_test*nc",
        }
    }


@pytest.fixture
def fake_filesystem():
    with Patcher() as patcher:
        patcher.fs.create_file("/path/to/test1.txt")
        patcher.fs.create_file("/path/to/test2.txt")
        patcher.fs.create_file("/path/to/fesom_test.nc")
        patcher.fs.create_file("/path/to/other_test123.nc")
        yield patcher


@pytest.fixture
def clean_environment():
    with mock.patch.dict(os.environ, {}, clear=True):
        yield


@pytest.mark.parametrize(
    "config, expected_output",
    [
        (
            config_bare,
            [
                pathlib.Path("/path/to/test1.txt"),
                pathlib.Path("/path/to/test2.txt"),
                pathlib.Path("/path/to/fesom_test.nc"),
                pathlib.Path("/path/to/other_test123.nc"),
            ],
        ),
        (
            config_only_env_name,
            [
                pathlib.Path("/path/to/test1.txt"),
                pathlib.Path("/path/to/test2.txt"),
                pathlib.Path("/path/to/fesom_test.nc"),
                pathlib.Path("/path/to/other_test123.nc"),
            ],
        ),
        (config_only_env_value, [pathlib.Path("/path/to/fesom_test.nc")]),
        (
            config_both,
            [pathlib.Path("/path/to/other_test123.nc")],
        ),
    ],
)
def test_listing_function(config, expected_output, fake_filesystem):
    output = input_files_in_path("/path/to", _input_pattern_from_env(config))
    # breakpoint()
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
    assert pattern.match("test")


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
    os.environ["CMOR_PATTERN"] = "test1*"
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


def test_subdirectories(config_bare, fake_filesystem, clean_environment):
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
