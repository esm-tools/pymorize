from datetime import datetime
from pathlib import Path

import xarray as xr
from loguru import logger


def convert_units(filepath: Path, source_units: str, target_units: str):
    """
    Converts the units of a NetCDF file, using the Pint library.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    source_units : str
    target_units : str
    """
    ds = xr.open_dataset(filepath)
    ds = ds.pint.quantify()
    ds = ds.pint.to(target_units)
    ds = ds.pint.dequantify()
    logger.info(f"Converted units of {filepath} from {source_units} to {target_units}")
    ds.to_netcdf(filepath)


def set_cmor_metadata(filepath: Path, cmor_metadata: dict, attrs_to_skip=[]):
    """
    Adds CMOR metadata to a NetCDF file.

    Parameters
    ----------
    filepath : Path
        Path to the input file.
    cmor_metadata : dict
        Dictionary with the CMOR metadata to be added to the file.
    attrs_to_skip : list of str, optional
        List of attributes to skip when adding CMOR metadata.
    """
    attrs_to_skip = attrs_to_skip or ["units", "cell_methods", "cell_measures"]
    ds = xr.open_dataset(filepath)
    for key, value in cmor_metadata.items():
        if key in attrs_to_skip:
            continue
        ds.attrs[key] = value
    hist_str = ds.attrs.get("history", "")
    hist_str += f"\n{datetime.now()}: CMOR metadata added by ``pymorize``\n"
    ds.to_netcdf(filepath)


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
