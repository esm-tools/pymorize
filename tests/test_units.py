import pint
import pytest

from pymorize.units import to_slash_notation, convert

si_notation_to_slash = [
    #  input          expected
    ("kg m-2 s-1",  "kg / m**2 / s**1"),
    ("kg m2",        "kg * m**2"),   
]

@pytest.mark.parametrize("test_input,expected", si_notation_to_slash)
def test_can_convert_SI_notation_to_slash_notation(test_input, expected):
    u = to_slash_notation(test_input)
    assert u == expected

mixed_notation_to_slash = [
    ("mmolC/m2/d", "mmolC / m**2 / d")
]

@pytest.mark.parametrize("test_input,expected", mixed_notation_to_slash)
def test_can_convert_mixed_notation_to_slash_notation(test_input, expected):
    u = to_slash_notation(test_input)
    assert u == expected

def test_can_convert_to_different_units():
    from_unit = 'mmolC/m2/d'
    to_unit = 'kg m-2 s-1'
    factor = convert(from_unit, to_unit)
    assert factor == 1.3901273148148146e-10

def test_non_slash_notation_raises_error():
    with pytest.raises(pint.errors.DimensionalityError):
        ureg = pint.UnitRegistry()
        ureg('kg m-2 s-1')

def test_without_defining_carbon_to_weight_conversion_raises_error():
    with pytest.raises(pint.errors.UndefinedUnitError):
        ureg = pint.UnitRegistry()
        ureg('mmolC/m**2/d')

def test_define_carbon_to_weight_conversion():
    ureg = pint.UnitRegistry()
    ureg.define("molC = 12.0107 * g")
    ureg('mmolC/m**2/d')