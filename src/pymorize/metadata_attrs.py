"""
This module contains library functions for setting metadata attributes.
"""

import xarray as xr


def set_global_attrs(data: xr.Dataset, rule):
    """
    Set global attributes for the given data based on the provided rule.

    Parameters
    ----------
    data : object
        The data object which contains attributes to be updated.
    rule : dict
        A dictionary containing rules for setting global attributes. It should
        have a key "global_attrs" which is a dictionary of attributes to override.

    Returns
    -------
    object
        The updated data object with global attributes set.
    """
    if not isinstance(data, xr.Dataset):
        raise ValueError("data must be an xarray.Dataset object.")
    global_attrs = rule.get("global_attrs", {})
    global_attrs = data.drv.global_attrs(override_dict=global_attrs)
    data.attrs.update(global_attrs)
    return data
