"""Tests for time averaging functionality."""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

import pymorize.std_lib.timeaverage
from pymorize.std_lib.timeaverage import compute_average


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    # Create a year of daily data
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    values = np.random.rand(len(dates))
    # Create chunked data array
    return xr.DataArray(values, coords={"time": dates}, dims=["time"]).chunk(
        {"time": 30}
    )  # Chunk by month


@pytest.fixture
def sample_rule():
    """Create a sample rule for testing."""

    class MockTable:
        def __init__(self, table_id, approx_interval, frequency=None):
            self.table_id = table_id
            self.approx_interval = approx_interval
            self.frequency = frequency

    class MockDataRequestVariable:
        def __init__(self, table):
            self.table = table

    class MockRule(dict):
        def __init__(self, table_id="Amon", approx_interval="30", frequency=None):
            super().__init__()
            self.data_request_variable = MockDataRequestVariable(
                MockTable(table_id, approx_interval, frequency)
            )

    return MockRule


def test_instantaneous_sampling(sample_data, sample_rule):
    """Test instantaneous sampling (first value of each period)."""
    rule = sample_rule("AmonPt", "30")  # Monthly instantaneous
    result = compute_average(sample_data, rule)

    # Should have 12 monthly values
    assert len(result) == 12
    # Each value should be the first value of the month
    assert pd.Timestamp("2023-01-01") in result.time.values
    assert pd.Timestamp("2023-02-01") in result.time.values


def test_mean_default_offset(sample_data, sample_rule):
    """Test mean with default offset (mid-point)."""
    rule = sample_rule("Amon", "30")  # Monthly mean
    result = compute_average(sample_data, rule)

    # Should have 12 monthly values
    assert len(result) == 12
    # Mid-month dates (approximately)
    times = pd.DatetimeIndex(result.time.values)
    assert times[0].strftime("%Y-%m-%d") == "2023-01-16"
    assert times[1].strftime("%Y-%m-%d") == "2023-02-14"


@pytest.mark.parametrize(
    "offset,expected_date",
    [
        (0.0, "2023-01-01"),  # Start of month
        (0.5, "2023-01-16"),  # Middle of month
        (1.0, "2023-01-31"),  # End of month
        ("first", "2023-01-01"),  # Start of month
        ("mid", "2023-01-16"),  # Middle of month
        ("last", "2023-01-31"),  # End of month
        ("14d", "2023-01-15"),  # Fixed 14 days offset
    ],
)
def test_mean_with_different_offsets(sample_data, sample_rule, offset, expected_date):
    """Test mean with various offset specifications."""
    rule = sample_rule("Amon", "30")  # Monthly mean
    rule["adjust_timestamp"] = offset
    result = compute_average(sample_data, rule)

    # Check January timestamp
    jan_time = pd.Timestamp(result.time.values[0])
    assert jan_time.strftime("%Y-%m-%d") == expected_date


def test_climatology_monthly(sample_data, sample_rule):
    """Test monthly climatology."""
    rule = sample_rule("AmonC", "30", frequency="monC")
    result = compute_average(sample_data, rule)

    # Should have 12 values (one per month)
    assert len(result) == 12
    # Should have month coordinate
    assert "month" in result.coords


def test_climatology_hourly(sample_data, sample_rule):
    """Test hourly climatology."""
    # Create hourly data first
    hourly_dates = pd.date_range("2023-01-01", "2023-01-07", freq="h")
    hourly_values = np.random.rand(len(hourly_dates))
    hourly_data = xr.DataArray(
        hourly_values, coords={"time": hourly_dates}, dims=["time"]
    ).chunk(
        {"time": 24}
    )  # Chunk by day

    rule = sample_rule("AmonCM", "30", frequency="1hrCM")
    result = compute_average(hourly_data, rule)

    # Should have 24 values (one per hour)
    assert len(result) == 24
    # Should have hour coordinate
    assert "hour" in result.coords


def test_invalid_climatology_frequency(sample_data, sample_rule):
    """Test invalid climatology frequency raises error."""
    rule = sample_rule("AmonC", "30", frequency="invalid")
    with pytest.raises(ValueError, match="Unknown Climatology"):
        compute_average(sample_data, rule)


FREQUENCY_TIME_METHOD = {
    "fx": "MEAN",
    "1hr": "MEAN",
    "3hr": "MEAN",
    "6hr": "MEAN",
    "day": "MEAN",
    "mon": "MEAN",
    "yr": "MEAN",
    "dec": "MEAN",
    "1hrPt": "INSTANTANEOUS",
    "subhrPt": "INSTANTANEOUS",
    "6hrPt": "INSTANTANEOUS",
    "3hrPt": "INSTANTANEOUS",
    "monPt": "INSTANTANEOUS",
    "yrPt": "INSTANTANEOUS",
    "1hrCM": "CLIMATOLOGY",
    "monC": "CLIMATOLOGY",
}


@pytest.mark.parametrize("frequency_name, expected", FREQUENCY_TIME_METHOD.items())
def test__get_time_method(frequency_name, expected):
    answer = pymorize.std_lib.timeaverage._get_time_method(frequency_name)
    assert answer == expected


def test__split_by_chunks_1d():
    # 1D array with chunks
    data = xr.DataArray(np.arange(10), dims="x").chunk({"x": 5})
    chunks = list(pymorize.std_lib.timeaverage._split_by_chunks(data))
    assert len(chunks) == 2  # Expecting 2 chunks for x dimension
    assert chunks[0][0] == {"x": slice(0, 5)}
    assert chunks[1][0] == {"x": slice(5, 10)}


def test__split_by_chunks_2d():
    # 2D array with chunks
    data = xr.DataArray(np.arange(100).reshape(10, 10), dims=("x", "y")).chunk(
        {"x": 5, "y": 2}
    )
    chunks = list(pymorize.std_lib.timeaverage._split_by_chunks(data))
    assert len(chunks) == 10  # Expecting 10 chunks (5 for x, 2 for y)
    assert chunks[0][0] == {"x": slice(0, 5), "y": slice(0, 2)}
    assert chunks[-1][0] == {"x": slice(5, 10), "y": slice(8, 10)}


def test__split_by_chunks_no_chunks():
    # Unchunked data should raise an informative error or handle gracefully
    data = xr.DataArray(np.arange(10), dims="x")
    # Split-by-chunks is meaningless if you have no chunks, so you should...
    # ...get back the same data?
    # assert data == pymorize.std_lib.timeaverage._split_by_chunks(data)
    # or
    # ...get an error? ValueError? The Chatbot agrees:
    # https://chatgpt.com/share/67458273-1368-8013-a1cc-7db511c18549
    with pytest.raises(ValueError):
        list(pymorize.std_lib.timeaverage._split_by_chunks(data))


def test__split_by_chunks_fesom_single_timestep(pi_uxarray_data):
    ds = xr.open_mfdataset(
        f for f in pi_uxarray_data.iterdir() if f.name.startswith("temp")
    )
    chunks = list(pymorize.std_lib.timeaverage._split_by_chunks(ds))
    # Only 1 file...
    assert len(chunks) == 1
    assert chunks[0][0] == {
        "time": slice(0, 1, None),
        "nz1": slice(0, 47, None),
        "nod2": slice(0, 3140, None),
    }


def test__split_by_chunks_fesom_example_data(fesom_2p6_pimesh_esm_tools_data):
    ds = xr.open_mfdataset(
        f
        for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
        if f.name.startswith("temp.fesom")
    )
    chunks = list(pymorize.std_lib.timeaverage._split_by_chunks(ds))
    # Expect 3 chunks, since we have 3 files in the example dataset
    assert len(chunks) == 3
    assert chunks[0][0] == {
        "time": slice(0, 1, None),
        "nz1": slice(0, 47, None),
        "nod2": slice(0, 3140, None),
    }
    assert chunks[1][0] == {
        "time": slice(1, 2, None),
        "nz1": slice(0, 47, None),
        "nod2": slice(0, 3140, None),
    }
    assert chunks[2][0] == {
        "time": slice(2, 3, None),
        "nz1": slice(0, 47, None),
        "nod2": slice(0, 3140, None),
    }


def test__frequency_from_approx_interval_decade():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("3650") == "10YE"
    )  # Decade conversion


def test__frequency_from_approx_interval_year():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("365") == "YE"
    )  # One year
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("1095") == "3YE"
    )  # Three years


def test__frequency_from_approx_interval_month():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("30") == "ME"
    )  # One month
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("60") == "2ME"
    )  # Two months


def test__frequency_from_approx_interval_day():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("1") == "D"
    )  # One day


def test__frequency_from_approx_interval_hour():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.04167") == "H"
    )  # Approximately one hour in days
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.08334") == "2H"
    )  # Approximately two hours in days
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.5") == "12H"
    )  # Half a day in hours


def test__frequency_from_approx_interval_minute():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.000694")
        == "min"
    )  # Approximately one minute in days
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.001388")
        == "2min"
    )  # Approximately two minutes in days
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.020833")
        == "30min"
    )  # Approximately half an hour in minutes


def test__frequency_from_approx_interval_second():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.00001157")
        == "s"
    )  # Approximately one second in days
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.00002314")
        == "2s"
    )  # Approximately two seconds in days
    assert not (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("0.000694")
        == "60s"
    )  # Approximately one minute in seconds, should give back min, since it can round up.


def test__frequency_from_approx_interval_millisecond():
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("1.1574e-8")
        == "ms"
    )  # Approximately one millisecond in days
    assert (
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("2.3148e-8")
        == "2ms"
    )  # Approximately two milliseconds in days


def test__invalid_interval():
    with pytest.raises(ValueError):
        pymorize.std_lib.timeaverage._frequency_from_approx_interval("not_a_number")


def test__compute_file_timespan_single_chunk():
    # Create a DataArray with a single chunk
    time = pd.date_range("2000-01-01", periods=10, freq="D")
    data = xr.DataArray(np.random.rand(10), dims="time", coords={"time": time})
    data = data.chunk({"time": 5})  # Single chunk

    assert pymorize.std_lib.timeaverage._compute_file_timespan(data) == 4


def test__compute_file_timespan_multiple_chunks():
    # Create a DataArray with multiple chunks
    time = pd.date_range("2000-01-01", periods=30, freq="D")
    data = xr.DataArray(np.random.rand(30), dims="time", coords={"time": time})
    data = data.chunk({"time": 10})

    assert pymorize.std_lib.timeaverage._compute_file_timespan(data) == 9


def test__compute_file_timespan_empty_time_dimension():
    # DataArray with an empty time dimension
    data = xr.DataArray(np.array([]), dims="time", coords={"time": []})
    with pytest.raises(ValueError, match="no time values in this chunk"):
        pymorize.std_lib.timeaverage._compute_file_timespan(data)


def test__compute_file_timespan_missing_time_dimension():
    # DataArray without a time dimension
    data = xr.DataArray(np.random.rand(10), dims="x")
    with pytest.raises(ValueError, match="missing the 'time' dimension"):
        pymorize.std_lib.timeaverage._compute_file_timespan(data)


def test__compute_file_timespan_non_sequential_time():
    # DataArray with non-sequential time points
    time = pd.to_datetime(["2000-01-01", "2000-01-05", "2000-01-20", "2000-01-30"])
    data = xr.DataArray(np.random.rand(4), dims="time", coords={"time": time})
    data = data.chunk({"time": 2})

    # FIXME: I'm not sure how to define this test for correctness...


def test__compute_file_timespan_large_dataarray():
    # DataArray with a larger number of chunks
    time = pd.date_range("2000-01-01", periods=100, freq="D")
    data = xr.DataArray(np.random.rand(100), dims="time", coords={"time": time})
    data = data.chunk({"time": 20})

    assert pymorize.std_lib.timeaverage._compute_file_timespan(data) == 19
