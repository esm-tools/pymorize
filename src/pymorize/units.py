"""
This module deals with the auto-unit conversion in the cmorization process.
In case the units in model files differ from CMIP Tables, this module attempts to
convert them automatically.

Conversion to-or-from a dimensionless quantity is ambiguous. In this case,
provide a mapping of what this dimensionless quantity represents and that
is used for the conversion. `data/dimensionless_mappings.yaml` contains some
examples on how the mapping is written.
"""

import re
import warnings
from typing import Pattern, Union

warnings.filterwarnings(
    "ignore", message=".*unavailable to set up matplotlib support.*"
)

import cf_xarray.units  # noqa: F401 # pylint: disable=unused-import
import pint_xarray
import xarray as xr
from chemicals import periodic_table

from .logging import logger
from .rule import Rule

ureg = pint_xarray.unit_registry


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


def handle_unit_conversion(da: xr.DataArray, rule: Rule) -> xr.DataArray:
    """Performs the unit-aware data conversion.

    If `source_unit` is provided, it is used instead of the unit from DataArray.

    Parameters
    ----------
    da: ~xr.DataArray
    unit: str
        unit to convert data to

    Returns
    -------
    ~xr.DataArray
        DataArray with units converted to `unit`.
    """
    if not isinstance(da, xr.DataArray):
        raise TypeError(f"Expected xr.DataArray, got {type(da)}")
    # data_request_variable needs to be defined at this point
    drv = rule.data_request_variable
    to_unit = drv.unit
    model_unit = rule.get("model_unit")
    from_unit = da.attrs.get("units")
    if model_unit is not None:
        logger.info(
            f"using user defined unit ({model_unit}) instead of ({from_unit}) from the original file"
        )
        from_unit = model_unit
    handle_chemicals(from_unit)
    handle_chemicals(to_unit)
    new_da = da.pint.quantify(from_unit)
    dimless = rule.get("dimensionless_unit_mappings", {})
    cmor_variable = rule.get("cmor_variable")
    if cmor_variable in dimless:
        _to_unit = dimless[cmor_variable][to_unit]
    else:
        _to_unit = to_unit
    if _to_unit == to_unit:
        logger.info(f"Converting units: ({da.name} -> {cmor_variable}) {from_unit} -> {to_unit}")
    else:
        logger.info(f"Converting units: ({da.name} -> {cmor_variable}) {from_unit} -> {_to_unit} ({to_unit})")
    new_da = new_da.pint.to(_to_unit).pint.dequantify()
    if new_da.attrs.get("units") != to_unit:
        logger.debug(
            "Pint auto-unit attribute setter different from requested unit string, setting manually."
        )
        new_da.attrs["units"] = to_unit
    # Ensure a units attribute is present, default to None (this should never happen)
    if "units" not in new_da.attrs:
        logger.warning(
            "Units attribute not present in DataArray after conversion, please check carefully!"
        )
        logger.warning("Setting to None")
        new_da.attrs["units"] = None
    return new_da
