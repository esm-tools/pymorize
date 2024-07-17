"""
This module deals with the auto-unit conversion in the cmorization process.
In case the units in model files differ from CMIP Tables, this module attempts to
convert them automatically.

In case of missing units in either model files or CMIP Tables, this module can
not convert from a dimentionless base to something with dimension. Dealing with
such thing have to done with `action` section in the Rules module on a per
variable basis.
"""

import re
from typing import Pattern

import pint
from chemicals import periodic_table
from loguru import logger

ureg = pint.UnitRegistry()
ureg.define("degC = degree_Celsius")
# https://ncics.org/portfolio/other-resources/udunits2/
ureg.define("degrees_east = deg")
ureg.define("degree_east = deg")
ureg.define("degrees_north = deg")
ureg.define("degree_north = deg")
ureg.define("degrees_west = -1 * deg")
ureg.define("degrees_south = -1 * deg")
# chemicals
# https://github.com/CalebBell/chemicals/
ureg.define(f"molN = {periodic_table.N.MW} * g")
ureg.define(f"molC = {periodic_table.C.MW} * g")
ureg.define(f"molFe = {periodic_table.Fe.MW} * g")


def _normalize_exponent_notation(
    s: str, pattern: Pattern = re.compile(r"(?P<name>\w+)-(?P<exp>\d+)")
):
    """Converts a string with exponents written as 'name-exp' into a more readable
    exponent notation 'name^-exp'.
    Example: 'm-2' gets converted as m^-2"
    """

    def correction(match):
        try:
            float(match.group())
        except ValueError:
            d = match.groupdict()
            s = f"{d['name']}^-{d['exp']}"
            return s
        return match.group()

    return re.sub(pattern, correction, s)


def _normalize_power_notation(
    s: str, pattern: Pattern = re.compile(r"(?P<name>\w+)(?P<exp>\d+)")
):
    """Converts a string with exponents written as 'nameexp' into a more readable
    exponent notation 'name^exp'.
    Example: 'm2' gets converted as m^2"
    """

    def correction(match):
        try:
            float(match.group())
        except ValueError:
            d = match.groupdict()
            s = f"{d[name]}^{d[exp]}"
            if d["exp"] == 1:
                s = f"{d['name']}"
            return s
        return match.group()

    return re.sub(pattern, correction, s)


def to_caret_notation(unit):
    "Formats the unit so Pint can understand them"
    return _normalize_power_notation(_normalize_exponent_notation(unit))


def calculate_unit_conversion_factor(a: str, b: str) -> float:
    """
    Returns the factor required to convert from unit "a" to unit "b"
    """
    try:
        A = ureg(a)
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        A = to_caret_notation(a)
        A = ureg(A)
    try:
        B = ureg(b)
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        B = to_caret_notation(b)
        B = ureg(B)
    logger.debug(A)
    logger.debug(B)
    return A.to(B).magnitude


def is_equal(a: str, b: str):
    "check if both 'a' and 'b' are equal"
    return ureg(to_caret_notation(a)) == ureg(to_caret_notation(b))
