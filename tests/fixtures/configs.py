import pytest


@pytest.fixture
def config(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def config_empty():
    return {"pymorize": {}}


@pytest.fixture
def config_pattern_env_var_name():
    return {
        "pymorize": {
            "pattern_env_var_name": "CMOR_PATTERN",
        }
    }


@pytest.fixture
def config_pattern_env_var_value():
    return {
        "pymorize": {
            "pattern_env_var_value": "test.*nc",
        }
    }


@pytest.fixture
def config_pattern_env_var_name_and_value():
    return {
        "pymorize": {
            "pattern_env_var_name": "CMOR_PATTERN",
            "pattern_env_var_value": "other_test.*nc",
        }
    }
