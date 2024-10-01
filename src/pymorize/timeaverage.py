#!/usr/bin/env python
"""
This module contains functions for time averaging of data arrays.

The approximate interval for time averaging is prescribed in the CMOR tables,
using the key ``'approx_interval'``. This information is also provided
in ~``pymorize.frequency``.

Functions
---------
_split_by_chunks(dataset: xr.DataArray) -> Tuple[Dict, xr.DataArray]:
    Split a large dataset into sub-datasets for each chunk.

_get_time_method(table_id: str) -> str:
    Determine the time method based on the table_id string.

_frequency_from_approx_interval(interval: str) -> str:
    Convert an interval expressed in days to a frequency string.

_compute_file_timespan(da: xr.DataArray) -> int:
    Compute the timespan of a given data array.

timeavg(da: xr.DataArray, rule: Dict) -> xr.DataArray:
    Time averages data with respect to time-method (mean/climatology/instant.)

Module Variables
----------------
_IGNORED_CELL_METHODS : list
    List of cell_methods to ignore when calculating time averages.

"""

import itertools

import pandas as pd
import xarray as xr

from .logging import logger


def _split_by_chunks(dataset: xr.DataArray):
    """
    Split a large dataset into sub-datasets for each chunk.

    This function is useful for handling large datasets that cannot fit into memory all at once.
    It yields a tuple containing the selection dictionary and the corresponding sub-dataset.

    Parameters
    ----------
    dataset : xr.DataArray
        The input dataset to be chunked. It can be either an xarray Dataset or DataArray.

    Yields
    ------
    tuple
        A tuple containing the selection dictionary and the corresponding sub-dataset.

    References
    ----------
    .. [1] https://github.com/pydata/xarray/issues/1093#issuecomment-259213382
    """
    chunk_slices = {}
    logger.info(f"{dataset.chunks=}")
    if isinstance(dataset, xr.Dataset):
        chunker = dataset.chunks
    elif isinstance(dataset, xr.DataArray):
        chunker = {dim: chunk for dim, chunk in zip(dataset.dims, dataset.chunks)}
    for dim, chunks in chunker.items():
        slices = []
        start = 0
        for chunk in chunks:
            stop = start + chunk
            slices.append(slice(start, stop))
            start = stop
        chunk_slices[dim] = slices
    for slices in itertools.product(*chunk_slices.values()):
        selection = dict(zip(chunk_slices.keys(), slices))
        yield (selection, dataset[selection])


def _get_time_method(table_id: str) -> str:
    """
    Determine the time method based on the table_id string.

    This function checks the ending of the table_id string and returns a corresponding time method.
    If the table_id ends with 'Pt', it returns 'INSTANTANEOUS'.
    If the table_id ends with 'C' or 'CM', it returns 'CLIMATOLOGY'.
    In all other cases, it returns 'MEAN'.

    Parameters
    ----------
    table_id : str
        The table_id string to check.

    Returns
    -------
    str
        The corresponding time method ('INSTANTANEOUS', 'CLIMATOLOGY', or 'MEAN').
    """
    if table_id.endswith("Pt"):
        return "INSTANTANEOUS"
    if table_id.endswith("C") or table_id.endswith("CM"):
        return "CLIMATOLOGY"
    return "MEAN"


def _frequency_from_approx_interval(interval: str):
    """
    Convert an interval expressed in days to a frequency string.

    This function takes an interval expressed in days and converts it to a frequency string
    in a suitable time unit (decade, year, month, day, hour, minute, second, millisecond).
    The conversion is based on an approximate number of days for each time unit.

    Parameters
    ----------
    interval : str
        The interval expressed in days.

    Returns
    -------
    str
        The frequency string in a suitable time unit.

    Raises
    ------
    ValueError
        If the interval cannot be converted to a float.
    """
    notation = [
        ("decade", lambda x: f"{x*10}YE" if x else "10YE", 3650),
        ("year", lambda x: f"{x}YE", 366),
        ("year", lambda x: f"{x}YE", 365),
        ("month", lambda x: f"{x}ME", 30),
        ("day", lambda x: f"{x}D", 1),
        ("hour", lambda x: f"{x}H", 24),
        ("minute", lambda x: f"{x}min", 24 * 60),
        ("second", lambda x: f"{x}s", 24 * 60 * 60),
        ("millisecond", lambda x: f"{x}ms", 24 * 60 * 60 * 1000),
    ]
    try:
        interval = float(interval)
    except ValueError:
        return interval
    to_divide = {"decade", "year", "month", "day"}
    for name, func, val in notation:
        if name in to_divide:
            value = interval // val
        else:
            value = interval * val
        if value >= 1:
            value = round(value)
            value = "" if value == 1 else value
            return func(value)


def _compute_file_timespan(da: xr.DataArray):
    """
    Compute the timespan of a given data array.

    This function splits the data array into chunks and computes the timespan of each chunk.
    The timespan of a chunk is defined as the difference between the last and the first time point in the chunk.
    The function returns the maximum timespan among all chunks.

    Parameters
    ----------
    da : xr.DataArray
        The data array to compute the timespan for.

    Returns
    -------
    int
        The maximum timespan among all chunks of the data array.

    """
    chunks = _split_by_chunks(da)
    tmp_file_timespan = []
    for i in range(3):
        try:
            subset_name, subset = next(chunks)
        except StopIteration:
            pass
        else:
            logger.info(f"{subset_name=}")
            logger.info(f"{subset.time.data[-1]=}")
            logger.info(f"{subset.time.data[0]=}")
            tmp_file_timespan.append(
                pd.Timedelta(subset.time.data[-1] - subset.time.data[0]).days
            )
    file_timespan = max(tmp_file_timespan)
    return file_timespan


def compute_average(da: xr.DataArray, rule):
    """
    Time averages data with respect to time-method (mean/climatology/instant.)

    This function takes a data array and a rule, computes the timespan of the data array, and then performs time averaging
    based on the time method specified in the rule. The time methods can be ``"INSTANTANEOUS"``,
    ``"MEAN"``, or ``"CLIMATOLOGY"``.

    Parameters
    ----------
    da : xr.DataArray
        The data array to compute the timespan for.
    rule : dict
        The rule dict containing the time method and other parameters.

    Returns
    -------
    xr.DataArray
        The time averaged data array.
    """
    file_timespan = _compute_file_timespan(da)
    rule.file_timespan = file_timespan
    drv = rule.data_request_variable
    approx_interval = drv.table.approx_interval
    approx_interval_in_hours = pd.offsets.Hour(float(approx_interval) * 24)
    frequency_str = _frequency_from_approx_interval(approx_interval)
    logger.debug(f"{approx_interval=} {frequency_str=}")
    # attach the frequency_str to rule, it is referenced when creating file name
    rule.frequency_str = frequency_str
    time_method = _get_time_method(drv.table.table_id)
    rule.time_method = time_method
    if time_method == "INSTANTANEOUS":
        ds = da.resample(time=frequency_str).first()
    elif time_method == "MEAN":
        ds = da.resample(time=frequency_str).mean()
        adjust_timestamp = rule.get("adjust_timestamp", True)
        if adjust_timestamp:
            offset = pd.Timedelta(approx_interval_in_hours / 2)
            logger.info(f"{offset=}")
            ds["time"] = ds.time.to_pandas() + offset
    elif time_method == "CLIMATOLOGY":
        if drv.table.frequency == "monC":
            ds = da.groupby("time.month").mean("time")
        elif drv.table.frequency == "1hrCM":
            ds = da.groupby("time.hour").mean("time")
        else:
            raise ValueError(
                f"Unknown Climatology {drv.table.frequency} in Table {drv.table.table_id}"
            )
    else:
        raise ValueError(f"Unknown time method: {time_method}")
    return ds


_IGNORED_CELL_METHODS = """
area: depth: time: mean
area: mean
area: mean (comment: over land and sea ice) time: point
area: mean time: maximum
area: mean time: maximum within days time: mean over days
area: mean time: mean within days time: mean over days
area: mean time: mean within hours time: maximum over hours
area: mean time: mean within years time: mean over years
area: mean time: minimum
area: mean time: minimum within days time: mean over days
area: mean time: point
area: mean time: sum
area: mean where crops time: maximum
area: mean where crops time: maximum within days time: mean over days
area: mean where crops time: minimum
area: mean where crops time: minimum within days time: mean over days
area: mean where grounded_ice_sheet
area: mean where ice_free_sea over sea time: mean
area: mean where ice_sheet
area: mean where land
area: mean where land over all_area_types time: mean
area: mean where land over all_area_types time: point
area: mean where land over all_area_types time: sum
area: mean where land time: mean
area: mean where land time: mean (with samples weighted by snow mass)
area: mean where land time: point
area: mean where sea
area: mean where sea depth: sum where sea (top 100m only) time: mean
area: mean where sea depth: sum where sea time: mean
area: mean where sea time: mean
area: mean where sea time: point
area: mean where sea_ice (comment: mask=siconc) time: point
area: mean where sector time: point
area: mean where snow over sea_ice area: time: mean where sea_ice
area: point
area: point time: point
area: sum
area: sum where ice_sheet time: mean
area: sum where sea time: mean
area: time: mean
area: time: mean (comment: over land and sea ice)
area: time: mean where cloud
area: time: mean where crops (comment: mask=cropFrac)
area: time: mean where floating_ice_shelf (comment: mask=sftflf)
area: time: mean where grounded_ice_sheet (comment: mask=sfgrlf)
area: time: mean where ice_sheet
area: time: mean where natural_grasses (comment: mask=grassFrac)
area: time: mean where pastures (comment: mask=pastureFrac)
area: time: mean where sea_ice (comment: mask=siconc)
area: time: mean where sea_ice (comment: mask=siconca)
area: time: mean where sea_ice (comment: mask=siitdconc)
area: time: mean where sea_ice_melt_pond (comment: mask=simpconc)
area: time: mean where sea_ice_ridges (comment: mask=sirdgconc)
area: time: mean where sector
area: time: mean where shrubs (comment: mask=shrubFrac)
area: time: mean where snow (comment: mask=snc)
area: time: mean where trees (comment: mask=treeFrac)
area: time: mean where unfrozen_soil
area: time: mean where vegetation (comment: mask=vegFrac)
longitude: mean time: mean
longitude: mean time: point
longitude: sum (comment: basin sum [along zig-zag grid path]) depth: sum time: mean
time: mean
time: mean grid_longitude: mean
time: point
""".strip().split(
    "\n"
)
"""list: cell_methods to ignore when calculating time averages"""
