import tempfile

import xarray as xr
from loguru import logger


def load_data(data, rule_spec, cmorizer):
    """
    A dummy function for testing. Loads the xarray tutorial data
    """
    logger.info("Loading data")
    data = xr.tutorial.open_dataset("air_temperature")
    return data


def logic_step(data, rule_spec, cmorizer):
    """
    A dummy function for testing. Prints data to screen and adds a dummy attribute to the data.
    """
    logger.info(data)
    logger.info("Adding dummy attribute to data")
    data.attrs["dummy_attribute"] = "dummy_value"
    logger.info(f"Data attributes: {data.attrs}")
    return data


def save_data(data, rule_spec, cmorizer):
    """
    A dummy function for testing. Saves the data to a netcdf file.
    """
    ofile = tempfile.mktemp(suffix=".nc")
    data.to_netcdf(ofile)
    logger.success(f"Data saved to {ofile}")
    return data
