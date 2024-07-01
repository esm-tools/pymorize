import pint
import tokenize
import io
import re
from collections import deque


"""
This module deals with the auto-unit conversion in the cmorization process.
In case the units in model files differ from CMIP Tables, this module attempts to convert them automatically.

In case of missing units in either model files or CMIP Tables, this module can not convert from a dimentionless base to something with dimension. Dealing with such thing have to done with `action` section in the Rules module on a per variable basis.

"""


#TODO: decide a place to hold the missing unit definitions that pint is not aware of
#from pathlib import Path 
#_unitsfile = Path(__file__).parent / "units_en.txt" 
#u = pint.UnitRegistry(_unitsfile)


ureg = pint.UnitRegistry()
#ureg.define('degC = degree_Celsius')
# https://ncics.org/portfolio/other-resources/udunits2/
ureg.define('degrees_east = deg')
ureg.define('degree_east = deg')
ureg.define('degrees_north = deg')
ureg.define('degree_north = deg')
ureg.define('degrees_west = -1 * deg')
ureg.define('degrees_south = -1 * deg')
# https://planetcalc.com/6777/
ureg.define('molN = 14.007 * g')
ureg.define('molC = 12.0107 * g')
ureg.define('molFe = 55.874 * g')


def fix_exponent_notation(s, pattern=re.compile(r'(?P<name>\w+)-(?P<exp>\d+)')):
    "kg m-2 -> kg / m^2"

    def correction(match):
        try:
            float(match.group())
        except ValueError:
            d = match.groupdict()
            s = "/ {0[name]}^{0[exp]}".format(d)
            if d["exp"] == "1":
                s = "/ {0[name]}".format(d)
            return s
        return match.group()

    s = re.sub(pattern, correction, s)
    if s.startswith('/'):
        s = "1 " + s
    return s

def fix_power_notation(s, pattern=re.compile(r"(?P<name>\w+)(?P<exp>\d+)")):
    "m2 -> m^2"
    def correction(match):
        try:
            float(match.group())
        except ValueError:
            d = match.groupdict()
            s = "{0[name]}^{0[exp]}".format(d)
            if d["exp"] == 1:
                s = "{0[name]}".format(d)
            return s
        return match.group()

    return re.sub(pattern, correction, s)


def to_slash_notation(unit):
    "Conver the units so Pint can understand them"
    return fix_power_notation(fix_exponent_notation(unit))


def convert(a: str, b: str) -> float:
    """
    Returns the factor required to convert from unit "a" to unit "b"
    """
    #print(a, b)
    try:
        A = ureg(a)
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        A = to_slash_notation(a)
        A = ureg(A)
    try:
        B = ureg(b)
    except (pint.errors.DimensionalityError, pint.errors.UndefinedUnitError):
        B = to_slash_notation(b)
        B = ureg(B)
    print(A, B)
    return A.to(B).magnitude


def is_equal(a: str, b: str):
    "check if both 'a' and 'b' are equal"
    return ureg(to_slash_notation(a)) == ureg(to_slash_notation(b))


def _quicktest():
    a = 1 * ureg.mmolC
    b = 1 * ureg.kg

    aa = 1 * ureg.mmolC /(ureg.m * ureg.m) / ureg.d
    bb = 1 * ureg.kg / (ureg.m * ureg.m) / ureg.s

    print(a.to(b))

    print(aa.to(bb))

    r = convert('mmolC/m2/d', 'kg m-2 s-1')
    print(r)

