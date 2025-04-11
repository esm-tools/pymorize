#!/usr/bin/env python
"""
This module contains functions for time averaging of data arrays.

The approximate interval for time averaging is prescribed in the CMOR tables,
using the key ``'approx_interval'``. This information is also provided
in ~``pymorize.frequency``.

Functions
---------
_split_by_chunks(dataset: xr.DataArray) -> Tuple[Dict, xr.DataArray]:
    Split a large dataset into sub-datasets for each chunk.

_get_time_method(table_id: str) -> str:
    Determine the time method based on the table_id string.

_frequency_from_approx_interval(interval: str) -> str:
    Convert an interval expressed in days to a frequency string.

_compute_file_timespan(da: xr.DataArray) -> int:
    Compute the timespan of a given data array.

timeavg(da: xr.DataArray, rule: Dict) -> xr.DataArray:
    Time averages data with respect to time-method (mean/climatology/instant.)

Module Variables
----------------
_IGNORED_CELL_METHODS : list
    List of cell_methods to ignore when calculating time averages.

"""

import itertools

import pandas as pd
import xarray as xr

from .logging import logger


def _split_by_chunks(dataset: xr.DataArray):
    """
    Split a large dataset into sub-datasets for each chunk.

    This function is useful for handling large datasets that cannot fit into memory all at once.
    It yields a tuple containing the selection dictionary and the corresponding sub-dataset.

    Parameters
    ----------
    dataset : xr.DataArray
        The input dataset to be chunked. It can be either an xarray Dataset or DataArray.

    Yields
    ------
    tuple
        A tuple containing the selection dictionary and the corresponding sub-dataset.

    References
    ----------
    .. [1] https://github.com/pydata/xarray/issues/1093#issuecomment-259213382
    """
    chunk_slices = {}
    logger.info(f"{dataset.chunks=}")
    if isinstance(dataset, xr.Dataset):
        chunker = dataset.chunks
    elif isinstance(dataset, xr.DataArray):
        chunker = {dim: chunk for dim, chunk in zip(dataset.dims, dataset.chunks)}
    for dim, chunks in chunker.items():
        slices = []
        start = 0
        for chunk in chunks:
            stop = start + chunk
            slices.append(slice(start, stop))
            start = stop
        chunk_slices[dim] = slices
    for slices in itertools.product(*chunk_slices.values()):
        selection = dict(zip(chunk_slices.keys(), slices))
        yield (selection, dataset[selection])


def _get_time_method(table_id: str) -> str:
    """
    Determine the time method based on the table_id string.

    This function checks the ending of the table_id string and returns a corresponding time method.
    If the table_id ends with 'Pt', it returns 'INSTANTANEOUS'.
    If the table_id ends with 'C' or 'CM', it returns 'CLIMATOLOGY'.
    In all other cases, it returns 'MEAN'.

    Parameters
    ----------
    table_id : str
        The table_id string to check.

    Returns
    -------
    str
        The corresponding time method ('INSTANTANEOUS', 'CLIMATOLOGY', or 'MEAN').
    """
    if table_id.endswith("Pt"):
        return "INSTANTANEOUS"
    if table_id.endswith("C") or table_id.endswith("CM"):
        return "CLIMATOLOGY"
    return "MEAN"


def _frequency_from_approx_interval(interval: str):
    """
    Convert an interval expressed in days to a frequency string.

    This function takes an interval expressed in days and converts it to a frequency string
    in a suitable time unit (decade, year, month, day, hour, minute, second, millisecond).
    The conversion is based on an approximate number of days for each time unit.

    Parameters
    ----------
    interval : str
        The interval expressed in days.

    Returns
    -------
    str
        The frequency string in a suitable time unit.

    Raises
    ------
    ValueError
        If the interval cannot be converted to a float.
    """
    notation = [
        ("decade", lambda x: f"{x*10}YS" if x else "10YS", 3650),
        ("year", lambda x: f"{x}YS", 366),
        ("year", lambda x: f"{x}YS", 365),
        ("month", lambda x: f"{x}MS", 30),
        ("day", lambda x: f"{x}d", 1),
        ("hour", lambda x: f"{x}h", 24),
        ("minute", lambda x: f"{x}min", 24 * 60),
        ("second", lambda x: f"{x}s", 24 * 60 * 60),
        ("millisecond", lambda x: f"{x}ms", 24 * 60 * 60 * 1000),
    ]
    try:
        interval = float(interval)
    except ValueError:
        return interval
    to_divide = {"decade", "year", "month", "day"}
    for name, func, val in notation:
        if name in to_divide:
            value = interval // val
        else:
            value = interval * val
        if value >= 1:
            value = round(value)
            value = "" if value == 1 else value
            return func(value)


def _compute_file_timespan(da: xr.DataArray):
    """
    Compute the timespan of a given data array.

    This function splits the data array into chunks and computes the timespan of each chunk.
    The timespan of a chunk is defined as the difference between the last and the first time point in the chunk.
    The function returns the maximum timespan among all chunks.

    Parameters
    ----------
    da : xr.DataArray
        The data array to compute the timespan for.

    Returns
    -------
    int
        The maximum timespan among all chunks of the data array.

    """
    chunks = _split_by_chunks(da)
    tmp_file_timespan = []
    for i in range(3):
        try:
            subset_name, subset = next(chunks)
        except StopIteration:
            pass
        else:
            logger.info(f"{subset_name=}")
            logger.info(f"{subset.time.data[-1]=}")
            logger.info(f"{subset.time.data[0]=}")
            tmp_file_timespan.append(
                pd.Timedelta(subset.time.data[-1] - subset.time.data[0]).days
            )
    file_timespan = max(tmp_file_timespan)
    return file_timespan


def compute_average(da: xr.DataArray, rule):
    """
    Time averages data with respect to time-method (mean/climatology/instant.)

    This function takes a data array and a rule, computes the timespan of the data array, and then performs time averaging
    based on the time method specified in the rule. The time methods can be ``"INSTANTANEOUS"``,
    ``"MEAN"``, or ``"CLIMATOLOGY"``.

    For ``"MEAN"`` time method, the timestamps can be adjusted using the ``adjust_timestamp`` parameter in the rule dict.
    This can be either:
    - A float between 0 and 1 representing the position within each period (e.g., 0.5 for mid-point)
    - A string preset: "first"/"start" (0.0), "last"/"end" (1.0), "mid"/"middle" (0.5)
    - A pandas offset string (e.g., "2d" for 2 days offset)
      This feature is useful for setting consistent mid-month dates by setting ``adjust_timestamp`` to "14d".

    Parameters
    ----------
    da : xr.DataArray
        The data array to compute the timespan for.
    rule : dict
        The rule dict containing the time method and other parameters.
        For "MEAN" time method, can include 'adjust_timestamp' to control timestamp positioning.

    Returns
    -------
    xr.DataArray
        The time averaged data array.
    """
    file_timespan = _compute_file_timespan(da)
    rule.file_timespan = file_timespan
    drv = rule.data_request_variable
    approx_interval = drv.table.approx_interval
    approx_interval_in_hours = pd.offsets.Hour(float(approx_interval) * 24)
    frequency_str = _frequency_from_approx_interval(approx_interval)
    logger.debug(f"{approx_interval=} {frequency_str=}")
    # attach the frequency_str to rule, it is referenced when creating file name
    rule.frequency_str = frequency_str
    time_method = _get_time_method(drv.table.table_id)
    rule.time_method = time_method
    if time_method == "INSTANTANEOUS":
        ds = da.resample(time=frequency_str).first()
    elif time_method == "MEAN":
        # First compute the mean using resample
        ds = da.resample(time=frequency_str).mean()
        # Get offset from adjust_timestamp, default to 0.5 (mid-point)
        offset = rule.get("adjust_timestamp", 0.5)
        offset_presets = {
            "first": 0,
            "start": 0,
            "last": 1,
            "end": 1,
            "mid": 0.5,
            "middle": 0.5,
        }   
        offset = offset_presets.get(offset, offset)
        try:
            offset = float(offset)
        except (TypeError, ValueError):
            # Use pandas offset string. example: offset="14d"
            ds['time'] = ds.time.to_series() + pd.tseries.frequencies.to_offset(offset)
        else:
            # Use custom_resample style offset calculation
            new_times = []
            for _, group in da.time.to_series().groupby(pd.Grouper(freq=frequency_str)):
                if not group.empty:
                    period_start = group.iloc[0]
                    period_end = group.iloc[-1]
                    new_timestamp = period_start + (period_end - period_start) * offset
                    new_times.append(new_timestamp)
            # Update the timestamps
            ds["time"] = pd.DatetimeIndex(new_times)
    elif time_method == "CLIMATOLOGY":
        if drv.table.frequency == "monC":
            ds = da.groupby("time.month").mean("time")
        elif drv.table.frequency == "1hrCM":
            ds = da.groupby("time.hour").mean("time")
        else:
            raise ValueError(
                f"Unknown Climatology {drv.table.frequency} in Table {drv.table.table_id}"
            )
    else:
        raise ValueError(f"Unknown time method: {time_method}")
    return ds


def custom_resample(df, freq="M", offset=0.5, func="mean"):
    """
    Resample a DataFrame and place timestamps at a custom offset within each period.

    Parameters
    ----------
    df : DataFrame
        DataFrame with a DatetimeIndex
    freq : str
        Frequency string (e.g., 'M' for month, 'Y' for year)
    offset : float
        Float between 0 and 1, representing the position within each period
    func : str
        Resampling function (e.g., 'mean', 'sum', 'max')

    Returns
    -------
    DataFrame
        Resampled DataFrame with adjusted timestamps

    Examples
    --------
    Each example is set up as follows:

        >>> date_rng = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        >>> df = pd.DataFrame({"value": np.random.rand(len(date_rng))}, index=date_rng)

    Resample to mid-month:

        >>> df_month_mid = custom_resample(df, freq="ME", offset=0.5)
        >>> print("Mid-month resampling:")
        >>> print(df_month_mid.head())
        Mid-month resampling:
                                value
        2023-01-16 00:00:00  0.402107
        2023-02-14 12:00:00  0.550212
        2023-03-16 00:00:00  0.496109
        2023-04-15 12:00:00  0.525329
        2023-05-16 00:00:00  0.554832

    Resample to mid-year:

        >>> df_year_mid = custom_resample(df, freq="YE", offset=0.5)
        >>> print("Mid-year resampling:")
        >>> print(df_year_mid)
            Mid-year resampling:
                           value
            2023-07-02  0.503732

    Resample to mid-week:

        >>> df_week_mid = custom_resample(df, freq="W", offset=0.5)
        >>> print("Mid-week resampling:")
        >>> print(df_week_mid.head())
        Mid-week resampling:
                       value
        2023-01-01  0.037969
        2023-01-05  0.400238
        2023-01-12  0.304294
        2023-01-19  0.435459
        2023-01-26  0.484908

    Resample to one-third through each month

        >>> df_month_third = custom_resample(df, freq="ME", offset=1 / 3)
        >>> print("One-third through each month:")
        >>> print(df_month_third.head())
        One-third through each month:
                                value
        2023-01-11 00:00:00  0.402107
        2023-02-10 00:00:00  0.550212
        2023-03-11 00:00:00  0.496109
        2023-04-10 16:00:00  0.525329
        2023-05-11 00:00:00  0.554832

    Resample to end of each quarter (equivalent to standard quarterly resampling)

        >>> df_quarter_end = custom_resample(df, freq="QE", offset=1)
        >>> print("Quarter-end resampling:")
        >>> print(df_quarter_end)
        Quarter-end resampling:
                       value
        2023-03-31  0.480563
        2023-06-30  0.525529
        2023-09-30  0.493180
        2023-12-31  0.515388


    Example with irregular time series:

        >>> irregular_dates = (
        >>>     pd.date_range("2023-01-01", periods=100, freq="D").tolist()
        >>>     + pd.date_range("2023-05-01", periods=50, freq="2D").tolist()
        >>>     + pd.date_range("2023-07-01", periods=30, freq="3D").tolist()
        >>> )
        >>> df_irregular = pd.DataFrame(
        >>>     {"value": np.random.rand(len(irregular_dates))}, index=irregular_dates
        >>> )
        >>> df_irregular_month = custom_resample(df_irregular, freq="ME", offset=0.5)
        >>> print("Irregular time series resampled to mid-month:")
        >>> print(df_irregular_month.head())
        Irregular time series resampled to mid-month:
                                value
        2023-01-16 00:00:00  0.500401
        2023-02-14 12:00:00  0.475774
        2023-03-16 00:00:00  0.495607
        2023-04-05 12:00:00  0.565798
        2023-05-16 00:00:00  0.597488

    """
    # Perform the resampling
    resampled = getattr(df.resample(freq), func)()

    # Adjust the timestamps
    new_index = []
    for name, group in df.groupby(pd.Grouper(freq=freq)):
        if not group.empty:
            period_start = group.index[0]
            period_end = group.index[-1]
            new_timestamp = period_start + (period_end - period_start) * offset
            new_index.append(new_timestamp)

    resampled.index = pd.DatetimeIndex(new_index)
    return resampled


_IGNORED_CELL_METHODS = """
area: depth: time: mean
area: mean
area: mean (comment: over land and sea ice) time: point
area: mean time: maximum
area: mean time: maximum within days time: mean over days
area: mean time: mean within days time: mean over days
area: mean time: mean within hours time: maximum over hours
area: mean time: mean within years time: mean over years
area: mean time: minimum
area: mean time: minimum within days time: mean over days
area: mean time: point
area: mean time: sum
area: mean where crops time: maximum
area: mean where crops time: maximum within days time: mean over days
area: mean where crops time: minimum
area: mean where crops time: minimum within days time: mean over days
area: mean where grounded_ice_sheet
area: mean where ice_free_sea over sea time: mean
area: mean where ice_sheet
area: mean where land
area: mean where land over all_area_types time: mean
area: mean where land over all_area_types time: point
area: mean where land over all_area_types time: sum
area: mean where land time: mean
area: mean where land time: mean (with samples weighted by snow mass)
area: mean where land time: point
area: mean where sea
area: mean where sea depth: sum where sea (top 100m only) time: mean
area: mean where sea depth: sum where sea time: mean
area: mean where sea time: mean
area: mean where sea time: point
area: mean where sea_ice (comment: mask=siconc) time: point
area: mean where sector time: point
area: mean where snow over sea_ice area: time: mean where sea_ice
area: point
area: point time: point
area: sum
area: sum where ice_sheet time: mean
area: sum where sea time: mean
area: time: mean
area: time: mean (comment: over land and sea ice)
area: time: mean where cloud
area: time: mean where crops (comment: mask=cropFrac)
area: time: mean where floating_ice_shelf (comment: mask=sftflf)
area: time: mean where grounded_ice_sheet (comment: mask=sfgrlf)
area: time: mean where ice_sheet
area: time: mean where natural_grasses (comment: mask=grassFrac)
area: time: mean where pastures (comment: mask=pastureFrac)
area: time: mean where sea_ice (comment: mask=siconc)
area: time: mean where sea_ice (comment: mask=siconca)
area: time: mean where sea_ice (comment: mask=siitdconc)
area: time: mean where sea_ice_melt_pond (comment: mask=simpconc)
area: time: mean where sea_ice_ridges (comment: mask=sirdgconc)
area: time: mean where sector
area: time: mean where shrubs (comment: mask=shrubFrac)
area: time: mean where snow (comment: mask=snc)
area: time: mean where trees (comment: mask=treeFrac)
area: time: mean where unfrozen_soil
area: time: mean where vegetation (comment: mask=vegFrac)
longitude: mean time: mean
longitude: mean time: point
longitude: sum (comment: basin sum [along zig-zag grid path]) depth: sum time: mean
time: mean
time: mean grid_longitude: mean
time: point
""".strip().split(
    "\n"
)
"""list: cell_methods to ignore when calculating time averages"""
