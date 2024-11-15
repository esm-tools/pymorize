import numpy as np
import pytest
import xarray as xr

from pymorize.cmorizer import CMORizer
from pymorize.data_request import DataRequestVariable
from pymorize.rule import Rule
from pymorize.units import handle_unit_conversion


def test_units_with_g_kg_to_0001_g_kg(rule_sos, CMIP_Tables_Dir):
    """Test the conversion of dimensionless units"""
    cmorizer = CMORizer(
        pymorize_cfg={
            "parallel": False,
        },
        general_cfg={"CMIP_Tables_Dir": CMIP_Tables_Dir},
        rules_cfg=[rule_sos],
    )
    da = xr.DataArray(10, name="sos", attrs={"units": "g/kg"})

    new_da = handle_unit_conversion(da, cmorizer.rules[0])
    assert new_da.attrs.get("units") == "0.001"
    # Check the magnitude of the data after conversion:
    assert np.equal(new_da.values, 10)


def test_units_with_g_g_to_0001_g_kg(rule_sos, CMIP_Tables_Dir):
    """Test the conversion of dimensionless units"""
    cmorizer = CMORizer(
        pymorize_cfg={
            "parallel": False,
        },
        general_cfg={"CMIP_Tables_Dir": CMIP_Tables_Dir},
        rules_cfg=[rule_sos],
    )
    da = xr.DataArray(10, name="sos", attrs={"units": "g/g"})

    new_da = handle_unit_conversion(da, cmorizer.rules[0])
    assert new_da.attrs.get("units") == "0.001"
    # Check the magnitude of the data after conversion:
    assert np.equal(new_da.values, 10000)
