import pytest

from tests.utils.constants import TEST_ROOT


@pytest.fixture
def CMIP_Tables_Dir():
    return TEST_ROOT / "data" / "cmip6-cmor-tables" / "Tables"


@pytest.fixture
def CMIP6_Oclim():
    return TEST_ROOT / "data" / "difmxybo2d" / "CMIP6_Oclim.json"
