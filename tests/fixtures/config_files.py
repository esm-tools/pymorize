import pytest

from tests.utils.constants import TEST_ROOT


@pytest.fixture
def test_config():
    return TEST_ROOT / "configs" / "test_config.yaml"


@pytest.fixture
def test_config_pi_uxarray():
    return TEST_ROOT / "configs" / "test_config_pi_uxarray.yaml"
