import pint
import pytest
from chemicals import periodic_table

from pymorize.units import (calculate_unit_conversion_factor,
                            to_caret_notation, ureg)

#  input samples that are found in CMIP6 tables and in fesom1 (recom)
allunits = [
    # input, expected
    ("%", "%"),
    ("(mol/kg) / atm", "(mol/kg) / atm"),
    ("0.001", "0.001"),
    ("1", "1"),
    ("1.e6 J m-1 s-1", "1.e^6 J m^-1 s^-1"),
    ("1e-06", "1e-06"),
    ("1e-09", "1e-09"),
    ("1e-12", "1e-12"),
    ("1e-3 kg m-2", "1e-3 kg m^-2"),
    ("1e-6 m s-1", "1e-6 m s^-1"),
    ("1e3 km3", "1e3 km^3"),
    ("1e6 km2", "1e6 km^2"),
    ("J m-2", "J m^-2"),
    ("K", "K"),
    ("K Pa s-1", "K Pa s^-1"),
    ("K m s-1", "K m s^-1"),
    ("K s-1", "K s^-1"),
    ("K2", "K^2"),
    ("N m-1", "N m^-1"),
    ("N m-2", "N m^-2"),
    ("Pa", "Pa"),
    ("Pa m s-2", "Pa m s^-2"),
    ("Pa s-1", "Pa s^-1"),
    ("Pa2 s-2", "Pa^2 s^-2"),
    ("W", "W"),
    ("W m-2", "W m^-2"),
    ("W/m2", "W/m^2"),
    ("day", "day"),
    ("degC", "degC"),
    ("degC kg m-2", "degC kg m^-2"),
    ("degC2", "degC^2"),
    ("degree", "degree"),
    ("degrees_east", "degrees_east"),
    ("degrees_north", "degrees_north"),
    ("kg", "kg"),
    ("kg kg-1", "kg kg^-1"),
    ("kg m-1 s-1", "kg m^-1 s^-1"),
    ("kg m-2", "kg m^-2"),
    ("kg m-2 s-1", "kg m^-2 s^-1"),
    ("kg m-3", "kg m^-3"),
    ("kg s-1", "kg s^-1"),
    ("km-2 s-1", "km^-2 s^-1"),
    ("m", "m"),
    ("m s-1", "m s^-1"),
    ("m s-1 d-1", "m s^-1 d^-1"),
    ("m s-2", "m s^-2"),
    ("m-1", "m^-1"),
    ("m-1 sr-1", "m^-1 sr^-1"),
    ("m-2", "m^-2"),
    ("m-3", "m^-3"),
    ("m2", "m^2"),
    ("m2 s-1", "m^2 s^-1"),
    ("m2 s-2", "m^2 s^-2"),
    ("m3", "m^3"),
    ("m3 s-1", "m^3 s^-1"),
    ("m3 s-2", "m^3 s^-2"),
    ("m4 s-1", "m^4 s^-1"),
    ("mmol/m2", "mmol/m^2"),
    ("mmol/m2/d", "mmol/m^2/d"),
    ("mmolC/(m2*d)", "mmolC/(m^2*d)"),
    ("mmolC/(m3*d)", "mmolC/(m^3*d)"),
    ("mmolC/d", "mmolC/d"),
    ("mmolC/m2/d", "mmolC/m^2/d"),
    ("mmolN/(m2*d)", "mmolN/(m^2*d)"),
    ("mmolN/d", "mmolN/d"),
    ("mmolN/m2/s", "mmolN/m^2/s"),
    ("mol m-2", "mol m^-2"),
    ("mol m-2 s-1", "mol m^-2 s^-1"),
    ("mol m-3", "mol m^-3"),
    ("mol m-3 s-1", "mol m^-3 s^-1"),
    ("mol mol-1", "mol mol^-1"),
    ("mol s-1", "mol s^-1"),
    ("mol/kg", "mol/kg"),
    ("s", "s"),
    ("s m-1", "s m^-1"),
    ("s-1", "s^-1"),
    ("s-2", "s^-2"),
    ("uatm", "uatm"),
    ("umolFe/m2/s", "umolFe/m^2/s"),
    ("year", "year"),
    ("yr", "yr"),
]


@pytest.mark.parametrize("test_input,expected", allunits)
def test_can_convert_SI_notation_to_caret_notation(test_input, expected):
    u = to_caret_notation(test_input)
    assert u == expected


mixed_notation_to_slash = [("mmolC/m2/d", "mmolC/m^2/d")]


@pytest.mark.parametrize("test_input,expected", mixed_notation_to_slash)
def test_can_convert_mixed_notation_to_caret_notation(test_input, expected):
    u = to_caret_notation(test_input)
    assert u == expected


def test_can_convert_to_different_units():
    from_unit = "mmolC/m2/d"
    to_unit = "kg m-2 s-1"
    factor = calculate_unit_conversion_factor(from_unit, to_unit)
    assert factor == 1.3901273148148146e-10


def test_non_caret_notation_raises_error():
    with pytest.raises(pint.errors.DimensionalityError):
        ureg("kg m-2 s-1")


def test_without_defining_uraninum_to_weight_conversion_raises_error():
    """Checks that only elements we added are defined"""
    with pytest.raises(pint.errors.UndefinedUnitError):
        ureg("mmolU/m**2/d")


def test_define_carbon_to_weight_conversion():
    assert "mmolC/m^2/d" in ureg
