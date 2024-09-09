"""
This module, `generic.py`, provides functionalities for transforming and standardizing NetCDF files
according to CMOR.

It contains several functions and classes:

Functions (can be used as actions in `Rule` objects):
- `linear_transform`: Applies a linear transformation to the data of a NetCDF file.
- `invert_z_axis`: Inverts the z-axis of a NetCDF file.

The Full CMOR (yes, bad pun):
    * Applied if no other rule sets are given for a file
    * Adds CMOR metadata to the file
    * Converts units
    * Performs time averaging
"""

import datetime
import tempfile
from pathlib import Path

import xarray as xr

from .logging import logger


def time_average(data, rule_spec, cmorizer, *args, **kwargs):
    if cmorizer["use_xarray_backend"]:
        data = data.resample(time=rule_spec["frequency"]).mean()
    else:
        # CDO Call
        pass
    return data


def load_data(data, rule_spec, cmorizer, *args, **kwargs):
    """Loads data described by the rule_spec."""
    ds_list = []
    for pattern in rule_spec["input_patterns"]:
        ds = xr.open_mfdataset(pattern, combine="by_coords")
        ds_list.append(ds)
    data = xr.concat(ds_list, dim="time")
    return data


def linear_transform(
    filepath: Path, execute: bool = False, slope: float = 1, offset: float = 0
):
    """
    Applies a linear transformation to the data of a NetCDF file.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    execute : bool, optional
    slope: float, optional
    offset: float, optional
    """
    if execute:
        ds = xr.open_dataset(filepath)
        ds = ds * slope + offset
        logger.info(f"Applied linear transformation to {filepath}")
        ds.to_netcdf(filepath)
    else:
        logger.info(f"Would apply linear transformation to {filepath}")
        logger.info(f"slope: {slope}, offset: {offset}")
        logger.info("Use `execute=True` to apply changes")


def invert_z_axis(filepath: Path, execute: bool = False, flip_sign: bool = False):
    """
    Inverts the z-axis of a NetCDF file.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    execute : bool, optional
        If True, the function will execute the inversion. If False, it will
        only print the changes that would be made.
    """
    if execute:
        ds = xr.open_dataset(filepath)
        ds = ds.reindex(z=ds.z[::-1])
        logger.info(f"Inverted order of z-axis of {filepath}")
        if flip_sign:
            ds["z"] *= -1
            logger.info(f"Flipped sign of z-axis of {filepath}")
        ds.to_netcdf(filepath)
    else:
        logger.info(f"Would invert z-axis of {filepath}")
        if flip_sign:
            logger.info("Would flip sign of z-axis")
        logger.info("Use `execute=True` to apply changes")


def create_cmor_directories(config: dict) -> dict:
    """
    Creates the directory structure for the CMORized files.

    Parameters
    ----------
    config : dict
        The pymorize configuration dictionary


    See Also
    --------
    https://docs.google.com/document/d/1h0r8RZr_f3-8egBMMh7aqLwy3snpD6_MrDz1q8n5XUk/edit
    """
    # Directory structure =
    # <mip_era>/
    #  <activity_id>/ # an exception for this exists in section "Directory structure template": "If multiple activities are listed in the global attribute, the first one is used in the directory structure."
    #   <institution_id>/
    #     <source_id>/
    #     <experiment_id>/
    #      <member_id>/
    #       <table_id>/
    #        <variable_id>/
    #         <grid_label>/
    #          <version>
    mip_era = config["mip_era"]
    activity_id = config["activity_id"]
    institution_id = config.get("institution_id", "AWI")
    source_id = config.get("source_id", "AWI-ESM-1-1-LR")
    experiment_id = config["experiment_id"]
    member_id = config["member_id"]
    table_id = config["table_id"]
    variable_id = config["variable_id"]
    grid_label = config["grid_label"]
    version = config["version"]

    output_root = config["output_root"]
    output_dir = (
        Path(output_root)
        / mip_era
        / activity_id
        / institution_id
        / source_id
        / experiment_id
        / member_id
        / table_id
        / variable_id
        / grid_label
        / version
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created directory structure for CMORized files in {output_dir}")
    config["output_dir"] = output_dir
    return config


def dummy_load_data(data, rule_spec, cmorizer, *args, **kwargs):
    """
    A dummy function for testing. Loads the xarray tutorial data
    """
    allowed_input_sources = ["xr_tutorial"]
    logger.info("Loading data")
    input_source = rule_spec.get("input_source", "xr_tutorial")
    if input_source == "xr_tutorial":
        data = xr.tutorial.open_dataset("air_temperature")
    else:
        raise NotImplementedError(f"Only {allowed_input_sources} are supported for now")
    if rule_spec.get("input_type") == "xr.DataArray":
        data = getattr(data, rule_spec.get("da_name", "air"))
    return data


def dummy_logic_step(data, rule_spec, cmorizer, *args, **kwargs):
    """
    A dummy function for testing. Prints data to screen and adds a dummy attribute to the data.
    """
    logger.info(data)
    logger.info("Adding dummy attribute to data")
    data.attrs["dummy_attribute"] = "dummy_value"
    logger.info(f"Data attributes: {data.attrs}")
    return data


def dummy_save_data(data, rule_spec, cmorizer, *args, **kwargs):
    """
    A dummy function for testing. Saves the data to a netcdf file.
    """
    ofile = tempfile.mktemp(suffix=".nc")
    data.to_netcdf(ofile)
    logger.success(f"Data saved to {ofile}")
    return data


def dummy_sleep(data, rule_spec, cmorizer, *arg, **kwargs):
    """
    A dummy function for testing. Sleeps for 5 seconds.
    """
    import time

    time.sleep(5)
    return data
