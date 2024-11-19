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
import cftime
import xarray as xr
import pandas as pd
import numpy as np

from .timeaverage import _frequency_from_approx_interval


def has_time_axis(ds):
    if get_time_label(ds) is not None:
        return True
    return False


def is_datetime_type(arr):
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
    for name, coord in ds.coords.items():
        if is_datetime_type(coord):
            # potential time label; exclude time_bnds
            if not coord.dims and is_scalar(coord):
                return name
            if name in coord.dims:
                return name
    else:
        return None


def needs_resampling(ds, timespan):
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
        The rule object containing information for generating the filepath.

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
    match frequency_str:
        case "yr" | "yrPt" | "dec":
            return f"{start:%Y}-{end:%Y}"
        case "mon" | "monC" | "monPt":
            return f"{start:%Y%m}-{end:%Y%m}"
        case "day":
            return f"{start:%Y%m%d}-{end:%Y%m%d}"
        case "6hr" | "3hr" | "1hr" | "6hrPt" | "3hrPt" | "1hrPt" | "1hrCM":
            _start = start.round("1min")
            _end = end.round("1min")
            return f"{_start:%Y%m%d%H%M}-{_end:%Y%m%d%H%M}"
        case "subhrPt":
            _start = start.round("1s")
            _end = end.round("1s")
            return f"{_start:%Y%m%d%H%M%S}-{_end:%Y%m%d%H%M%S}"
        case "fx":
            return ""
        case _:
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

    This function generates a filepath for the output file based on the given dataset and rule.
    The filepath includes the name, table_id, institution, source_id, experiment_id, label, grid, and optionally the start and end time.

    Parameters
    ----------
    ds : xarray.Dataset
        The input dataset.
    rule : Rule
        The rule object containing information for generating the filepath.

    Returns
    -------
    str
        The generated filepath.

    Notes
    -----
    The rule object should have the following attributes: cmor_variable, data_request_variable, variant_label, source_id, experiment_id, output_directory, and optionally institution.
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
    return filepath


def save_dataset(da: xr.DataArray, rule):
    """
    save datasets to multiple files

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
