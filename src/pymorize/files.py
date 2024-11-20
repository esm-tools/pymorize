"""
This module contains functions for handling file-related operations in the pymorize package.
It includes functions for creating filepaths based on given rules and datasets, and for
saving the resulting datasets to the generated filepaths.



Table 2: Precision of time labels used in file names
|---------------+-------------------+-----------------------------------------------|
| Frequency     | Precision of time | Notes                                         |
|               | label             |                                               |
|---------------+-------------------+-----------------------------------------------|
| yr, dec,      | “yyyy”            | Label with the years recorded in the first    |
| yrPt          |                   | and last coordinate values.                   |
|---------------+-------------------+-----------------------------------------------|
| mon, monC     | “yyyyMM”          | For “mon”, label with the months recorded in  |
|               |                   | the first and last coordinate values; for     |
|               |                   | “monC” label with the first and last months   |
|               |                   | contributing to the climatology.              |
|---------------+-------------------+-----------------------------------------------|
| day           | “yyyyMMdd”        | Label with the days recorded in the first and |
|               |                   | last coordinate values.                       |
|---------------+-------------------+-----------------------------------------------|
| 6hr, 3hr,     | “yyyyMMddhhmm”    | Label 1hrCM files with the beginning of the   |
| 1hr,          |                   | first hour and the end of the last hour       |
| 1hrCM, 6hrPt, |                   | contributing to climatology (rounded to the   |
| 3hrPt,        |                   | nearest minute); for other frequencies in     |
| 1hrPt         |                   | this category, label with the first and last  |
|               |                   | time-coordinate values (rounded to the        |
|               |                   | nearest minute).                              |
|---------------+-------------------+-----------------------------------------------|
| subhrPt       | “yyyyMMddhhmmss”  | Label with the first and last time-coordinate |
|               |                   | values (rounded to the nearest second)        |
|---------------+-------------------+-----------------------------------------------|
| fx            | Omit time label   | This frequency applies to variables that are  |
|               |                   | independent of time (“fixed”).                |
|---------------+-------------------+-----------------------------------------------|

"""

from collections import deque
from pathlib import Path

import cftime
import numpy as np
import pandas as pd
import xarray as xr

from .timeaverage import _frequency_from_approx_interval


def has_time_axis(ds):
    """
    Checks if the given dataset has a time axis.

    Parameters
    ----------
    ds : xarray.Dataset or xarray.DataArray
        The dataset to check.

    Returns
    -------
    bool
        True if the dataset has a time axis, False otherwise.
    """
    if get_time_label(ds) is not None:
        return True
    return False


def is_datetime_type(arr):
    """
    Checks if the given numpy array or xarray DataArray is of datetime type.

    Parameters
    ----------
    arr : numpy.array or xarray.DataArray
        The input array to check.

    Returns
    -------
    bool
        ``True`` if `arr` is of datetime type, ``False`` otherwise.

    Notes
    -----
    This function checks if the input array is of numpy datetime64 type or
    if it is of cftime datetime type. If the array is of neither type, it
    returns ``False``.
    """
    try:
        if np.issubdtype(arr, np.datetime64):
            return True
    except TypeError:
        if isinstance(arr.item(0), tuple(cftime._cftime.DATE_TYPES.values())):
            return True
    return False


def is_scalar(da):
    return xr.core.utils.is_scalar(da)


def get_time_label(ds):
    """
    Determines the name of the coordinate in the dataset that can serve as a time label.

    Parameters
    ----------
    ds : xarray.Dataset
        The dataset containing coordinates to check for a time label.

    Returns
    -------
    str or None
        The name of the coordinate that is a datetime type and can serve as a time label,
        or None if no such coordinate is found.
    """
    label = deque()
    for name, coord in ds.coords.items():
        if not is_datetime_type(coord):
            continue
        if not coord.dims:
            continue
        if name in coord.dims:
            label.appendleft(name)
        else:
            label.append(name)
    label.append(None)
    return label.popleft()


def needs_resampling(ds, timespan):
    """
    Checks if a given dataset needs resampling based on its time axis.

    Parameters
    ----------
    ds : xr.Dataset or xr.DataArray
        The dataset to check.
    timespan : str
        The time span for which the dataset is to be resampled.
        10YS, 1YS, 6MS, etc.

    Returns
    -------
    bool
        True if the dataset needs resampling, False otherwise.
    """
    if timespan is None:
        return False
    if not timespan:
        return False
    time_label = get_time_label(ds)
    if time_label is None:
        return False
    if is_scalar(ds[time_label]):
        return False
    start = pd.Timestamp(ds[time_label].data[0])
    end = pd.Timestamp(ds[time_label].data[-1])
    offset = pd.tseries.frequencies.to_offset(timespan)
    return (start + offset) < end


def _filename_time_range(ds, rule) -> str:
    """
    Determine the time range used in naming the file.

    Parameters
    ----------
    ds : xarray.Dataset
        The input dataset.
    rule : Rule
        The rule object containing information for generating the
        filepath.

    Returns
    -------
    str
        time_range in filepath.
    """
    if not has_time_axis(ds):
        return ""
    time_label = get_time_label(ds)
    if is_scalar(ds[time_label]):
        return ""
    start = pd.Timestamp(ds[time_label].data[0])
    end = pd.Timestamp(ds[time_label].data[-1])
    frequency_str = rule.get("frequency_str")
    if frequency_str in ("yr", "yrPt", "dec"):
        return f"{start:%Y}-{end:%Y}"
    if frequency_str in ("mon", "monC", "monPt"):
        return f"{start:%Y%m}-{end:%Y%m}"
    if frequency_str == "day":
        return f"{start:%Y%m%d}-{end:%Y%m%d}"
    if frequency_str in ("6hr", "3hr", "1hr", "6hrPt", "3hrPt", "1hrPt", "1hrCM"):
        _start = start.round("1min")
        _end = end.round("1min")
        return f"{_start:%Y%m%d%H%M}-{_end:%Y%m%d%H%M}"
    if frequency_str == "subhrPt":
        _start = start.round("1s")
        _end = end.round("1s")
        return f"{_start:%Y%m%d%H%M%S}-{_end:%Y%m%d%H%M%S}"
    if frequency_str == "fx":
        return ""
    else:
        raise NotImplementedError(f"No implementation for {frequency_str} yet.")

    # # NOTE: the commented out return statments: Although they report the actual
    # # time limits in the file, the hard-coded version is chosen 2 reason,
    # # a) to replicate code in seamore tool
    # # b) to have consistent time range scheme in filename (Hmmm.... ?)
    # if frequency_str is None:
    #     return f"{start_year}-{end_year}"
    # if frequency_str.endswith("YE"):
    #     return f"{start_year}-{end_year}"
    # if frequency_str.endswith("ME"):
    #     # return f"{start.strftime('%Y%m')}-{end.strftime('%Y%m')}"
    #     return f"{start_year}01-{end_year}12"
    # if frequency_str.endswith("D"):
    #     # return f"{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
    #     return f"{start_year}0101-{end_year}1231"
    # if frequency_str.endswith("H"):
    #     # return f"{start.strftime('%Y%m%d%H')}-{end.strftime('%Y%m%d%H')}"
    #     if time_method == "INSTANTANEOUS":
    #         return f"{start_year}01010030-{end_year}12312330"
    #     else:
    #         return f"{start_year}01010000-{end_year}12312300"
    # # the following is not covered in seamore tool, hopefully they are used.
    # if frequency_str.endswith("min"):
    #     return f"{start.strftime('%Y%m%d%H%M')}-{end.strftime('%Y%m%d%H%M')}"
    # else:
    #     return f"{start.strftime('%Y%m%d%H%M%S')}-{end.strftime('%Y%m%d%H%M%S')}"


def create_filepath(ds, rule):
    """
    Generate a filepath when given an xarray dataset and a rule.

    This function generates a filepath for the output file based on
    the given dataset and rule.  The filepath includes the name,
    table_id, institution, source_id, experiment_id, label, grid, and
    optionally the start and end time.

    Parameters
    ----------
    ds : xarray.Dataset
        The input dataset.
    rule : Rule
        The rule object containing information for generating the
        filepath.

    Returns
    -------
    str
        The generated filepath.

    Notes
    -----
    The rule object should have the following attributes:
    cmor_variable, data_request_variable, variant_label, source_id,
    experiment_id, output_directory, and optionally institution.
    """
    name = rule.cmor_variable
    table_id = rule.data_request_variable.table.table_id  # Omon
    label = rule.variant_label  # r1i1p1f1
    source_id = rule.source_id  # AWI-CM-1-1-MR
    experiment_id = rule.experiment_id  # historical
    out_dir = rule.output_directory  # where to save output files
    institution = rule.get("institution", "AWI")
    grid = "gn"  # grid_type
    time_range = _filename_time_range(ds, rule)
    filepath = f"{out_dir}/{name}_{table_id}_{institution}-{source_id}_{experiment_id}_{label}_{grid}_{time_range}.nc"
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    return filepath


def save_dataset(da: xr.DataArray, rule):
    """
    Save dataset to one or more files.

    Parameters
    ----------
    da : xr.DataArray
        The dataset to be saved.
    rule : Rule
        The rule object containing information for generating the
        filepath.

    Returns
    -------
    None

    Notes
    -----
    If the dataset does not have a time axis, or if the time axis is a scalar,
    this function will save the dataset to a single file.  Otherwise, it will
    split the dataset into chunks based on the time axis and save each chunk
    to a separate file.

    The filepath will be generated based on the rule object and the time range
    of the dataset.  The filepath will include the name, table_id, institution,
    source_id, experiment_id, label, grid, and optionally the start and end time.

    If the dataset needs resampling (i.e., the time axis does not align with the
    time frequency specified in the rule object), this function will split the
    dataset into chunks based on the time axis and resample each chunk to the
    specified frequency.  The resampled chunks will then be saved to separate
    files.

    NOTE: prior to calling this function, call dask.compute() method,
    otherwise tasks will progress very slow.
    """
    if not has_time_axis(da):
        filepath = create_filepath(da, rule)
        return da.to_netcdf(filepath, mode="w", format="NETCDF4")
    time_label = get_time_label(da)
    if is_scalar(da[time_label]):
        filepath = create_filepath(da, rule)
        return da.to_netcdf(filepath, mode="w", format="NETCDF4")
    if isinstance(da, xr.DataArray):
        da = da.to_dataset()
    file_timespan = rule.file_timespan
    frequency_str = _frequency_from_approx_interval(file_timespan)
    if not needs_resampling(da, frequency_str):
        filepath = create_filepath(da, rule)
        return da.to_netcdf(filepath, mode="w", format="NETCDF4")
    groups = da.resample(time=frequency_str)
    paths = []
    datasets = []
    for group_name, group_ds in groups:
        paths.append(create_filepath(group_ds, rule))
        datasets.append(group_ds)
    return xr.save_mfdataset(datasets, paths)
