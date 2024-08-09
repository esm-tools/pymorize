"""
This module deals with the auto-unit conversion in the cmorization process.
In case the units in model files differ from CMIP Tables, this module attempts to
convert them automatically.

In case of missing units in either model files or CMIP Tables, this module can
not convert from a dimentionless base to something with dimension. Dealing with
such thing have to done with `action` section in the Rules module on a per
variable basis.

Additionally, the cmip frequencies are mapped here. The CMIP6 frequency
names and corresponding number of days are available as a dictionary in the 
``CMIP_FREQUENCIES`` variable. Assignment of these frequencies to the unit registry
can be done with the ``assign_frequency_to_unit_registry`` function.
"""

import re
from typing import Pattern, Union

import cf_xarray.units
import pint_xarray
import xarray as xr
from chemicals import periodic_table

from .frequency import CMIP_FREQUENCIES
from .logging import logger

ureg = pint_xarray.unit_registry


def assign_frequency_to_unit_registry():
    """Assign the CMIP6 frequencies to the unit registry."""
    for freq_name, days in CMIP_FREQUENCIES.items():
        ureg.define(f"{freq_name} = {days} * d")


def handle_chemicals(
    s: Union[str, None] = None, pattern: Pattern = re.compile(r"mol(?P<symbol>\w+)")
):
    """Registers known chemical elements definitions to global ``ureg`` (unit registry)

    Parameters
    ----------
    s: str or None
        string to search for chemical elements based upon the symbol, e.g. ``C`` for carbon.
    pattern: re.Pattern
        compiled regex pattern to search for chemical elements. This should contain a
        `named group <https://docs.python.org/3/howto/regex.html#non-capturing-and-named-groups>`_ ``symbol``
        to extract the symbol of the chemical element from a potentially larger string.

    Raises
    ------
    ValueError
        If the chemical element is not found in the periodic table.

    See Also
    --------
    ~chemicals.elements.periodic_table: Periodic table of elements
    ~re.compile: `Python's regex syntax <https://docs.python.org/3/library/re.html#regular-expression-syntax>`_.
    """
    if s is None:
        return
    match = pattern.search(s)
    if match:
        d = match.groupdict()
        try:
            element = getattr(periodic_table, d["symbol"])
        except AttributeError:
            raise ValueError(
                f"Unknown chemical element {d.groupdict()['symbol']} in {d.group()}"
            )
        else:
            try:
                ureg(s)
            except pint_xarray.pint.errors.UndefinedUnitError:
                logger.debug(f"Chemical element {element.name} detected in units {s}.")
                logger.debug(
                    f"Registering definition: {match.group()} = {element.MW} * g"
                )
                ureg.define(f"{match.group()} = {element.MW} * g")


# FIXME: This needs to have a different signature!
def handle_unit_conversion(
    da: xr.DataArray,
    rule_spec,
    cmorizer,
    source_unit: Union[str, None] = None,
) -> xr.DataArray:
    """Performs the unit-aware data conversion.

    If `source_unit` is provided, it is used instead of the unit from DataArray.

    Parameters
    ----------
    da: ~xr.DataArray
    unit: str
        unit to convert data to
    source_unit: str or None
        Override the unit on ``da.attrs.unit`` if needed.

    Returns
    -------
    ~xr.DataArray
        DataArray with units converted to `unit`.
    """
    unit = getattr(rule_spec, "cmor_units", None)
    from_unit = da.attrs.get("units")
    if source_unit is not None:
        logger.debug(
            f"using user defined unit ({source_unit}) instead of ({from_unit}) from DataArray "
        )
        from_unit = source_unit
    handle_chemicals(from_unit)
    handle_chemicals(unit)
    new_da = da.pint.quantify(from_unit)
    new_da = new_da.pint.to(unit).pint.dequantify()
    logger.debug(f"setting units on DataArray: {unit}")
    new_da.attrs["units"] = unit
    return new_da
