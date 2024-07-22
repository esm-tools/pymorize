import numpy as np
import pint
import pytest
import xarray as xr
from chemicals import periodic_table

from pymorize.units import handle_chemicals, handle_unit_conversion, ureg

#  input samples that are found in CMIP6 tables and in fesom1 (recom)
allunits = [
    "%",
    "0.001",
    "1",
    "1.e6 J m-1 s-1",
    "1e-06",
    "1e-3 kg m-2",
    "1e3 km3",
    "J m-2",
    "K",
    "K Pa s-1",
    "K s-1",
    "K2",
    "Pa2 s-2",
    "W m^-2",
    "W/m2",
    "W/m^2",
    "day",
    "degC",
    "degC kg m-2",
    "degC2",
    "degree",
    "degrees_east",
    "degrees_north",
    "kg kg-1",
    "kg m-2 s-1",
    "kg m-3",
    "kg s-1",
    "km-2 s-1",
    "m-1 sr-1",
    "m-2",
    "m^-3",
    "m^2",
    "mol/kg",
    "mol/m2",
    "mol m-2",
    "mol m^-2",
    "(mol/kg) / atm",
    "mmol/m2/d",
    "uatm",
    "year",
    "yr",
]


@pytest.mark.parametrize("test_input", allunits)
def test_can_read_units(test_input):
    ureg(test_input)


units_with_chemical_element = [
    "mmolC/(m2*d)",
    "mmolC/d",
    "mmolC/m2/d",
    "mmolN/(m2*d)",
    "mmolN/d",
    "umolFe/m2/s",
]


@pytest.mark.parametrize("test_input", units_with_chemical_element)
def test_handle_chemicals(test_input):
    """Ensures the unit registry can add new units when parsed by ``handle_chemicals``."""
    handle_chemicals(test_input)
    ureg(test_input)


def test_can_handle_simple_chemical_elements():
    from_unit = "molC"
    to_unit = "g"
    da = xr.DataArray(10, attrs={"units": from_unit})
    new_da = handle_unit_conversion(da, to_unit)
    assert new_da.data == np.array(periodic_table.Carbon.MW * 10)
    assert new_da.attrs["units"] == to_unit


def test_can_handle_chemical_elements():
    from_unit = "mmolC/m2/d"
    to_unit = "kg m-2 s-1"
    da = xr.DataArray(10, attrs={"units": from_unit})
    new_da = handle_unit_conversion(da, to_unit)
    assert np.allclose(new_da.data, np.array(1.39012731e-09))
    assert new_da.attrs["units"] == to_unit


def test_user_defined_units_takes_precedence_over_units_in_dataarray():
    from_unit = "molC"
    to_unit = "g"
    da = xr.DataArray(10, attrs={"units": "kg"})
    # here, "molC" will be used instead of "kg"
    new_da = handle_unit_conversion(da, to_unit, from_unit)
    assert new_da.data == np.array(periodic_table.Carbon.MW * 10)
    assert new_da.attrs["units"] == to_unit


def test_without_defining_uraninum_to_weight_conversion_raises_error():
    """Checks that only elements we added are defined"""
    with pytest.raises(pint.errors.UndefinedUnitError):
        ureg("mmolU/m**2/d")


def test_recognizes_previous_defined_chemical_elements():
    assert "mmolC/m^2/d" in ureg


def test_works_when_both_units_are_None():
    to_unit = None
    da = xr.DataArray(10, attrs={"units": None})
    new_da = handle_unit_conversion(da, to_unit)
    assert new_da.attrs["units"] == to_unit


def test_works_when_both_units_are_empty_string():
    to_unit = ""
    da = xr.DataArray(10, attrs={"units": ""})
    new_da = handle_unit_conversion(da, to_unit)
    assert new_da.attrs["units"] == to_unit


@pytest.mark.parametrize("from_unit", ["m/s", None, ""])
def test_when_target_units_is_None_overrides_existing_units(from_unit):
    to_unit = None
    da = xr.DataArray(10, attrs={"units": from_unit})
    new_da = handle_unit_conversion(da, to_unit)
    assert new_da.attrs["units"] == to_unit


@pytest.mark.parametrize("from_unit", ["m/s", None])
def test_when_tartget_unit_is_empty_string_raises_error(from_unit):
    to_unit = ""
    da = xr.DataArray(10, attrs={"units": from_unit})
    with pytest.raises(ValueError):
        handle_unit_conversion(da, to_unit)
