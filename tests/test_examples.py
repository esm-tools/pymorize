"""
Examples of how to use various parts of the testing framework.
"""

import pytest


def test_nothing():
    """
    This is a test that does nothing.
    """
    pass


@pytest.mark.parametrize(
    "config",
    [
        "config_empty",
        "config_pattern_env_var_name",
        "config_pattern_env_var_value",
        "config_pattern_env_var_name_and_value",
    ],
    indirect=True,
)
def test_using_config(config):
    """
    This test demonstrates how to use the dynamic config fixture.
    """
    print(f"Using config: {config}")
    pass
