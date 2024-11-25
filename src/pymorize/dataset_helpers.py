from collections import deque

import cftime
import numpy as np
import pandas as pd
from xarray.core.utils import is_scalar


def is_datetime_type(arr: np.ndarray) -> bool:
    "Checks if array elements are datetime objects or cftime objects"
    return isinstance(
        arr.item(0), tuple(cftime._cftime.DATE_TYPES.values())
    ) or np.issubdtype(arr, np.datetime64)


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

    Example
    -------
    >>> ds = xr.Dataset({'time': ('time', pd.date_range('2000-01-01', periods=10))})
    >>> get_time_label(ds)
    'time'
    >>> ds = xr.DataArray(np.ones(10), coords={'T': ('time', pd.date_range('2000-01-01', periods=10))})
    >>> get_time_label(ds)
    'T'
    >>> # The following does have a valid time coordinate, expected to return None
    >>> da = xr.Dataset({'time': ('time', [1,2,3,4,5])})
    >>> get_time_label(da)
    None
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


def has_time_axis(ds) -> bool:
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
    return bool(get_time_label(ds))


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

    Notes:
    ------
    After time-averaging step, this function aids in determining if
    splitting into multiple files is requied based on provided
    timespan.
    """
    if (timespan is None) or (not timespan):
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