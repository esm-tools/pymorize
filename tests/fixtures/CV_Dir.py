import pytest

from tests.utils.constants import TEST_ROOT


@pytest.fixture
def CV_dir():
    return TEST_ROOT / "data" / "CV" / "CMIP6_CVs"
