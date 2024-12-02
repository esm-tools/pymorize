"""
Tests for DataRequestVariable
"""

from pymorize.data_request.variable import CMIP6JSONDataRequestVariable


def test_init():
    drv = CMIP6JSONDataRequestVariable.from_json_file(
        "cmip6-cmor-tables/Tables/CMIP6_Omon.json",
        "thetao",
    )
    assert drv.name == "thetao"
    assert drv.frequency == "mon"
    assert drv.table_name == "Omon"
