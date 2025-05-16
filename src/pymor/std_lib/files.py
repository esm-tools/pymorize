"""
This module contains functions for handling file-related operations in the pymor package.
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

from pathlib import Path

import pandas as pd
import xarray as xr
from xarray.core.utils import is_scalar

from .dataset_helpers import get_time_label, has_time_axis, needs_resampling


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
    start = pd.Timestamp(str(ds[time_label].data[0]))
    end = pd.Timestamp(str(ds[time_label].data[-1]))
    # frequency_str = rule.get("frequency_str")
    frequency_str = rule.data_request_variable.frequency
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
    table_id = rule.data_request_variable.table_header.table_id  # Omon
    label = rule.variant_label  # r1i1p1f1
    source_id = rule.source_id  # AWI-CM-1-1-MR
    experiment_id = rule.experiment_id  # historical
    out_dir = rule.output_directory  # where to save output files
    institution = rule.get("institution", "AWI")
    grid = "gn"  # grid_type
    time_range = _filename_time_range(ds, rule)
    # check if output sub-directory is needed
    enable_output_subdirs = rule._pymor_cfg.get("enable_output_subdirs", False)
    if enable_output_subdirs:
        subdirs = rule.ga.subdir_path()
        out_dir = f"{out_dir}/{subdirs}"
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
    time_dtype = rule._pymor_cfg("xarray_time_dtype")
    time_unlimited = rule._pymor_cfg("xarray_time_unlimited")
    extra_kwargs = {}
    if time_unlimited:
        extra_kwargs.update({"unlimited_dims": ["time"]})
    time_encoding = {"dtype": time_dtype}
    time_encoding = {k: v for k, v in time_encoding.items() if v is not None}
    if not has_time_axis(da):
        filepath = create_filepath(da, rule)
        return da.to_netcdf(
            filepath,
            mode="w",
            format="NETCDF4",
        )
    time_label = get_time_label(da)
    if is_scalar(da[time_label]):
        filepath = create_filepath(da, rule)
        return da.to_netcdf(
            filepath,
            mode="w",
            format="NETCDF4",
            encoding={time_label: time_encoding},
            **extra_kwargs,
        )
    if isinstance(da, xr.DataArray):
        da = da.to_dataset()
    # Not sure about this, maybe it needs to go above, before the is_scalar
    # check
    if rule._pymor_cfg("xarray_time_set_standard_name"):
        da[time_label].attrs["standard_name"] = "time"
    if rule._pymor_cfg("xarray_time_set_long_name"):
        da[time_label].attrs["long_name"] = "time"
    if rule._pymor_cfg("xarray_time_enable_set_axis"):
        time_axis_str = rule._pymor_cfg("xarray_time_taxis_str")
        da[time_label].attrs["axis"] = time_axis_str
    if rule._pymor_cfg("xarray_time_remove_fill_value_attr"):
        time_encoding["_FillValue"] = None

    file_timespan = getattr(rule, "file_timespan", None)
    if not needs_resampling(da, file_timespan):
        filepath = create_filepath(da, rule)
        return da.to_netcdf(
            filepath,
            mode="w",
            format="NETCDF4",
            encoding={time_label: time_encoding},
            **extra_kwargs,
        )
    groups = da.resample(time=file_timespan)
    paths = []
    datasets = []
    for group_name, group_ds in groups:
        paths.append(create_filepath(group_ds, rule))
        datasets.append(group_ds)
    return xr.save_mfdataset(
        datasets,
        paths,
        encoding={time_label: time_encoding},
        **extra_kwargs,
    )
