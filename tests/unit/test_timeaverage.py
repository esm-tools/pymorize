"""Tests for time averaging functionality."""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from pymorize.timeaverage import compute_average


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    # Create a year of daily data
    dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
    values = np.random.rand(len(dates))
    # Create chunked data array
    return xr.DataArray(
        values, 
        coords={"time": dates}, 
        dims=["time"]
    ).chunk({"time": 30})  # Chunk by month


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


@pytest.mark.parametrize("offset,expected_date", [
    (0.0, "2023-01-01"),       # Start of month
    (0.5, "2023-01-16"),      # Middle of month
    (1.0, "2023-01-31"),      # End of month
    ("first", "2023-01-01"),   # Start of month
    ("mid", "2023-01-16"),    # Middle of month
    ("last", "2023-01-31"),   # End of month
    ("14d", "2023-01-15"),    # Fixed 14 days offset 
])
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
        hourly_values, 
        coords={"time": hourly_dates}, 
        dims=["time"]
    ).chunk({"time": 24})  # Chunk by day
    
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
