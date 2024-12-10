import pytest

from tests.utils.constants import TEST_ROOT


@pytest.fixture
def test_config_cmip6():
    return TEST_ROOT / "configs" / "test_config_cmip6.yaml"


@pytest.fixture
def test_config_cmip7():
    return TEST_ROOT / "configs" / "test_config_cmip7.yaml"


@pytest.fixture
def pi_uxarray_config():
    return TEST_ROOT / "configs" / "test_config_pi_uxarray.yaml"


@pytest.fixture
def fesom_2p6_pimesh_esm_tools_config():
    return TEST_ROOT / "configs" / "test_config_fesom_2p6_pimesh.yaml"
