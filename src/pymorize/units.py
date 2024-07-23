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
from typing import Pattern, Union

import cf_xarray.units
import pint_xarray
import xarray as xr
from chemicals import periodic_table
from loguru import logger

ureg = pint_xarray.unit_registry


def handle_chemicals(
    s: Union[str, None] = None, pattern: Pattern = re.compile(r"mol(?P<symbol>\w+)")
):
    """Registers known chemical elements definitions to global ureg (unit registry)"""
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


def handle_unit_conversion(
    da: xr.DataArray, unit: str, source_unit: Union[str, None] = None
) -> xr.DataArray:
    """Performs the unit-aware data conversion.

    If `source_unit` is provided, it is used instead of the unit from DataArray.

    Parameters:
    -----------
    da: xr.DataArray
    unit: unit to convert data to
    source_unit: Override the unit on xr.DataArray if needed.
    """
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
