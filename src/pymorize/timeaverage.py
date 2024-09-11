# timeaverage.py

import xarray as xr
import pandas as pd


"""
The approximate_interval for time averaging is prescribed in the cmor tables.

In each table header approx_interval is provided. This information is also
provided in frequency.py
"""


def monthly_mean(da: xr.DataArray):
    """Monthly means per year.

    In usual pratice, da.groupby('time.month').mean("time") does monthly means
    over multiple years.  For instance, doing a monthly mean on a 5 year dataset
    results in collapsing all years to 12 months (12 timesteps).  This function
    preserves years, i.e., a 5 year dataset * 12 months => 60 timesteps.
    """
    t = da.resample(time="ME").mean("time")
    return t


# what should be the signature of the `monthly_mean` function?
# consider the following part in the config file
# model_variable: salt
#    model_units: PSU
#    cmor_variable: so
#    cmor_table: CMIP6_Omon.json
#    input_patterns:

# in this case, the function signature could be as follows
# def monthy_mean(model_variable: str, config: dict) -> xr.DataArray:
#     ...
# For a given model_variable, the required parameters are retried from config file:
# - from cmor_table, approx_interval is read
# - from input_patterns, xr.Dataset object is created from multiple files.

# concerns:
# - constructing xr.Dataset from xr.open_mfdataset("test*.nc") should be handled
#   by some other function and not in timeaverage.py. The reason being, the
#   unknown data volume (memory footprint) of the "test*.nc". Does this fit in a
#   single node?

# Question regarding config file: If a variable is found in more than one table,
# and the user wishes to process them all, Can that be expressed in a single
# config file? If so, the above function signature may not be appropriate.
# changing the signature to...
# def monthy_mean(model_variable: str, cmor_table: json, config: dict) -> xr.DataArray:
#    ...
