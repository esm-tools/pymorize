"""
Standard library for the pymorize package.

This module provides commonly used functions and utilities for
manipulating and standardizing climate model output data.
"""

# Dataset helper functions
from .dataset_helpers import (
    get_time_label,
    has_time_axis,
    is_datetime_type,
    needs_resampling,
)

# Data transformation utilities
from .generic import (
    create_cmor_directories,
    get_variable,
    invert_z_axis,
    linear_transform,
    load_data,
    multiyear_monthly_mean,
    resample_monthly,
    resample_yearly,
    trigger_compute,
)

# Attribute management
from .global_attributes import (
    CMIP6GlobalAttributes,
    CMIP7GlobalAttributes,
    GlobalAttributes,
    set_global_attributes,
)

# Time averaging functionality
from .timeaverage import _frequency_from_approx_interval, compute_average

# Unit manipulation
from .units import convert_units, get_standard_units, is_dimensional
from .variable_attributes import set_variable_attrs

__all__ = [
    # Data transformation
    "linear_transform",
    "invert_z_axis",
    "create_cmor_directories",
    "load_data",
    "get_variable",
    "resample_monthly",
    "resample_yearly",
    "multiyear_monthly_mean",
    "trigger_compute",
    # Time averaging
    "compute_average",
    "_frequency_from_approx_interval",
    # Dataset helpers
    "is_datetime_type",
    "get_time_label",
    "has_time_axis",
    "needs_resampling",
    # Attribute management
    "GlobalAttributes",
    "CMIP6GlobalAttributes",
    "CMIP7GlobalAttributes",
    "set_global_attributes",
    "set_variable_attrs",
    # Unit management
    "convert_units",
    "get_standard_units",
    "is_dimensional",
]
