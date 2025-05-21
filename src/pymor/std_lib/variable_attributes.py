"""
Pipeline steps to attach metadata attributes to the xarrays
"""

from typing import Union

import xarray as xr

from ..core.logging import logger
from ..core.rule import Rule


def set_variable_attrs(
    ds: Union[xr.Dataset, xr.DataArray], rule: Rule
) -> Union[xr.Dataset, xr.DataArray]:
    """
    Uses the Rule object's associated data_request_variable to set the variable
    attributes of the xarray object.

    Parameters
    ----------
    ds : Union[xr.Dataset, xr.DataArray]
        The xarray Dataset or DataArray to which the variable attributes will be applied.
    rule : Rule
        The Rule object containing the data_request_variable with the attributes to be set.

    Returns
    -------
    Union[xr.Dataset, xr.DataArray]
        The xarray Dataset or DataArray with updated attributes.

    Raises
    ------
    TypeError
        If the input is not an xarray Dataset or DataArray.
        If the given data type is not an xarray Dataset or DataArray.

    Notes
    -----
    This function updates the attributes of the given xarray object based on the attributes
    defined in the data_request_variable of the provided Rule object. It also handles the
    setting of missing values and optionally skips setting the unit attribute based on the
    configuration in the Rule object.
    """
    if isinstance(ds, xr.Dataset):
        given_dtype = xr.Dataset
        da = ds[rule.model_variable]
    elif isinstance(ds, xr.DataArray):
        given_dtype = xr.DataArray
        da = ds
    else:
        raise TypeError("Input must be an xarray Dataset or DataArray")

    # Use the associated data_request_variable to set the variable attributes
    missing_value = rule._pymor_cfg("xarray_default_missing_value")
    attrs = rule.data_request_variable.attrs
    for attr in ["missing_value", "_FillValue"]:
        if attrs[attr] is None:
            attrs[attr] = missing_value
    skip_setting_unit_attr = rule._pymor_cfg("xarray_skip_unit_attr_from_drv")
    if skip_setting_unit_attr:
        attrs.pop("units", None)
    logger.info("Setting the following attributes:")
    for k, v in attrs.items():
        logger.info("f * {k}: {v}")
    da.attrs.update(attrs)

    # Update the encoding for missing values:
    if "missing_value" in attrs:
        da.encoding.update({"_FillValue": attrs["missing_value"]})

    if given_dtype == xr.Dataset:
        # Assume it was updated via reference
        # ds.variables[rule.model_variable] = da
        return ds
    elif given_dtype == xr.DataArray:
        return da
    else:
        raise TypeError(
            "Given data type is not an xarray Dataset or DataArray, refusing to continue!"
        )


# Alias name for the function
set_variable_attributes = set_variable_attrs
