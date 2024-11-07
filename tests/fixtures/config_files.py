import pytest

from tests.utils.constants import TEST_ROOT


@pytest.fixture
def test_config():
    return TEST_ROOT / "configs" / "test_config.yaml"


@pytest.fixture
def fesom_pi_mesh_config_file():
    return TEST_ROOT / "configs/fesom_pi_mesh_run.yaml"
