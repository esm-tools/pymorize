import os
import re
from unittest import mock

import pytest

from pymorize.gather_inputs import _input_pattern_from_env


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


@mock.patch.dict(os.environ, {}, clear=True)
def test_default_pattern(config_bare):
    pattern = _input_pattern_from_env(config_bare)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test")


@mock.patch.dict(os.environ, {"CMOR_PATTERN": "test.*"}, clear=True)
def test_custom_pattern_name(config_only_env_name):
    pattern = _input_pattern_from_env(config_only_env_name)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test123")
    assert not pattern.match("123test")


@mock.patch.dict(os.environ, {}, clear=True)
def test_custom_pattern_value(config_only_env_value):
    pattern = _input_pattern_from_env(config_only_env_value)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test")


@mock.patch.dict(os.environ, {}, clear=True)
def test_custom_both(config_both):
    pattern = _input_pattern_from_env(config_both)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("other_test123.nc")
    os.environ["CMOR_PATTERN"] = "test.*"
    pattern = _input_pattern_from_env(config_both)
    assert isinstance(pattern, re.Pattern)
    assert pattern.match("test123")
    assert not pattern.match("123test")
