"""
Tests for DataRequestVariable
"""

import pathlib

import pytest

from pymorize.data_request.variable import CMIP6DataRequestVariable


def test_variable_from_cmip6_table():
    table = pathlib.Path("cmip6-cmor-tables/Tables/CMIP6_Omon.json")
    variable = "thetao"
    drv = CMIP6DataRequestVariable.from_json_table_file(table, variable)
    assert drv.frequency == "mon"
    assert drv.table_name == "Omon"
