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
from pathlib import Path

import xarray as xr
from loguru import logger


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

    Directory structure =
     <mip_era>/
      <activity_id>/ # an exception for this exists in section "Directory structure template": "If multiple activities are listed in the global attribute, the first one is used in the directory structure."
       <institution_id>/
         <source_id>/
         <experiment_id>/
          <member_id>/
           <table_id>/
            <variable_id>/
             <grid_label>/
              <version>

    Parameters
    ----------
    config : dict
        The pymorize configuration dictionary


    See Also
    --------
    https://docs.google.com/document/d/1h0r8RZr_f3-8egBMMh7aqLwy3snpD6_MrDz1q8n5XUk/edit
    """
    mip_era = config["mip_era"]
    activity_id = config["activity_id"]
    institution_id = config.get(
        "institution_id", "Alfred Wegener Institure for Polar and Marine Research"
    )
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
