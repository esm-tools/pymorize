"""
This module, `generic.py`, provides functionalities for transforming and standardizing NetCDF files
according to CMOR.

It contains several functions and classes:

Functions (can be used as actions in `Rule` objects):
- `linear_transform`: Applies a linear transformation to the data of a NetCDF file.
- `invert_z_axis`: Inverts the z-axis of a NetCDF file.

Classes:
- `Rule`: Defines a set of instructions to process a file and convert it to a CMOR standard.
- `CMORMetadata`: Inherits from `Rule` and adds CMOR metadata to a NetCDF file.
- `CMORizer`: Manages a set of `Rule` objects and applies them to NetCDF files.

Each `Rule` object represents a set of transformations that should be applied to a NetCDF file to
make it comply with the CMOR standard. The `CMORizer` class manages a collection of `Rule` objects and
applies the appropriate ones to each file.

The `CMORMetadata` class is a special type of `Rule` that adds CMOR metadata to a file.

The Full CMOR (yes, bad pun):
    * Applied if no other rule sets are given for a file
    * Adds CMOR metadata to the file
    * Converts units
    * Performs time averaging
"""

import datetime
import json
import re
import sys
from functools import partial
from pathlib import Path

import questionary
import xarray as xr
import yaml
from loguru import logger

from .utils import generate_partial_function, get_callable_by_name
