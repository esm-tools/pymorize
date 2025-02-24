"""
Pipeline steps to attach metadata attributes to the xarrays
"""

from typing import Union

import xarray as xr

from .rule import Rule


def set_variable_attrs(
    ds: Union[xr.Dataset, xr.DataArray], rule: Rule
) -> Union[xr.Dataset, xr.DataArray]:
    """Uses the Rule object's associated data_request_variable to set the variable attributes of the xarray object"""
    if isinstance(ds, xr.Dataset):
        given_dtype = xr.Dataset
        da = ds[rule.model_variable]
    elif isinstance(ds, xr.DataArray):
        given_dtype = xr.DataArray
        da = ds
    else:
        raise TypeError("Input must be an xarray Dataset or DataArray")

    # Use the associated data_request_variable to set the variable attributes
    missing_value = rule._pymorize_cfg("xarray_default_missing_value")
    attrs = rule.data_request_variable.attrs
    for attr in ["missing_value", "_FillValue"]:
        if attrs[attr] is None:
            attrs[attr] = missing_value
    skip_setting_unit_attr = rule._pymorize_cfg("xarray_skip_unit_attr_from_drv")
    if skip_setting_unit_attr:
        attrs.pop("units", None)
    da.attrs.update(rule.data_request_variable.attrs)

    # Update the encoding for missing values:
    if "missing_value" in rule.data_request_variable.attrs:
        da.encoding.update(
            {"_FillValue": rule.data_request_variable.attrs["missing_value"]}
        )

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
