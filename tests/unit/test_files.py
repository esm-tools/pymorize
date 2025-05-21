from pymor.std_lib.files import file_timespan_tail, get_offset, split_data_timespan
from unittest.mock import Mock
import pandas as pd
import xarray as xr
import numpy as np
import tempfile
import pytest


@pytest.mark.parametrize(
    "adjust_timestamp,expected",
    [
        ("mid", pd.Timedelta(15, unit="d")),
        ("last", pd.Timedelta(30, unit="d")),
        ("first", pd.Timedelta(0, unit="d")),
        ("start", pd.Timedelta(0, unit="d")),
        ("end", pd.Timedelta(30, unit="d")),
        ("14D", pd.Timedelta(14, unit="d")),
        ("0.5", pd.Timedelta(15, unit="d")),
        ("0.25", pd.Timedelta(7.5, unit="d")),
        ("0.75", pd.Timedelta(22.5, unit="d")),
        (None, None),
    ],
)
def test_get_offset(adjust_timestamp, expected):
    rule = Mock()
    rule.data_request_variable.table_header.approx_interval = "30"
    rule.adjust_timestamp = adjust_timestamp
    assert get_offset(rule) == expected


def test_file_timespan_tail_no_offset():
    rule = Mock()
    rule.data_request_variable.table_header.approx_interval = "30"
    rule.adjust_timestamp = None
    timeindex = xr.cftime_range("2001", periods=120, freq="MS", calendar="standard")
    air = xr.Dataset(
        data_vars=dict(
            air=(("time", "ncells"), np.random.rand(timeindex.size, 10)),
        ),
        coords=dict(
            time=timeindex,
            ncells=np.arange(10),
        ),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        for group_name, group in air.groupby("time.year"):
            filename = f"{tmpdir}/air_{group_name}.nc"
            files.append(filename)
            group.to_netcdf(filename)
        rule.inputs = [
            Mock(files=files)
        ]
        tails = file_timespan_tail(rule)
    timestamps = []
    for group_name, group in air.groupby("time.year"):
        timestamps.append(group.time.values[-1])
    assert tails == timestamps


def test_file_timespan_tail_with_offset():
    rule = Mock()
    rule.data_request_variable.table_header.approx_interval = "30"
    rule.adjust_timestamp = "mid"
    timeindex = xr.cftime_range("2001", periods=120, freq="MS", calendar="standard")
    air = xr.Dataset(
        data_vars=dict(
            air=(("time", "ncells"), np.random.rand(timeindex.size, 10)),
        ),
        coords=dict(
            time=timeindex,
            ncells=np.arange(10),
        ),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        for group_name, group in air.groupby("time.year"):
            filename = f"{tmpdir}/air_{group_name}.nc"
            files.append(filename)
            group.to_netcdf(filename)
        rule.inputs = [
            Mock(files=files)
        ]
        tails = file_timespan_tail(rule)
    timestamps = []
    offset = get_offset(rule)
    for group_name, group in air.groupby("time.year"):
        timestamps.append(group.time.values[-1] + offset)
    assert set(tails) == set(timestamps)


def test_split_data_timespan():
    rule = Mock()
    rule.data_request_variable.table_header.approx_interval = "30"
    rule.adjust_timestamp = "mid"
    # creating 2 years data with daily frequency
    timeindex = xr.cftime_range("2000", periods=365*2, freq="D", calendar="standard")
    air = xr.Dataset(
        data_vars=dict(
            air=(("time", "ncells"), np.random.rand(timeindex.size, 10)),
        ),
        coords=dict(
            time=timeindex,
            ncells=np.arange(10),
        ),
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        # split time into yearly chunks
        for group_name, group in air.resample(time="YS"):
            filename = f"{tmpdir}/air_{group_name}.nc"
            files.append(filename)
            group.to_netcdf(filename)
        rule.inputs = [
            Mock(files=files)
        ]
        # resample to monthly frequency and calculate mean (simulate cmorize)
        ds = air.resample(time="MS").mean(dim="time")
        offset = get_offset(rule)
        if offset is not None:
            ds["time"] = ds.time + offset
        chunks = split_data_timespan(ds, rule)
        # check if chunks are in the correct time range
        tails = file_timespan_tail(rule)
        for chunk, timestamp in zip(chunks, tails):
            assert all(bool(ts < timestamp) for ts in chunk.time.values)
        # another approch is to check the year in chunk. It needs to unique and single value.
        for chunk in chunks:
            assert len(set(chunk.time.dt.year.values)) == 1
            assert len(set(chunk.time.dt.month.values)) == 12