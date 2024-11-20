"""Tests for saving dataset

General guide lines
===================

1. setgrid function returns `xr.Dataset` object if appropriate grid
   file is provided. Otherwise the data is still a `xr.DataArray`
   object.  This means saving data function should support both
   objects.

2. If data has chunks, then each chunk must be saved in a separate
   file.  When opening multiple files with `xr.mfdataset`, chunks are
   automatically created (one chunk per file)

3. If user provides a chunk size (timespan), it must be used instead.

4. When saving data to multiple files, save data function is also
   responsible for creating appropriate filenames. The time span
   (period) of each file is reflected in the filename but it is not
   the exact time span. It is snapped to the closest interval relative
   to data frequency. Tests should include checks for time span in the
   filename.

5. Avoid unnecessary data resampling when not required. Example: in a
   single time step dataset.


Table 2: Precision of time labels used in file names
|---------------+-------------------+-----------------------------------------------|
| Frequency     | Precision of time | Notes                                         |
|               | label             |                                               |
|---------------+-------------------+-----------------------------------------------|
| yr, dec,      | “yyyy”            | Label with the years recorded in the first    |
| yrPt          |                   | and last coordinate values.                   |
|---------------+-------------------+-----------------------------------------------|
| mon, monC     | “yyyyMM”          | For “mon”, label with the months recorded in  |
|               |                   | the first and last coordinate values; for     |
|               |                   | “monC” label with the first and last months   |
|               |                   | contributing to the climatology.              |
|---------------+-------------------+-----------------------------------------------|
| day           | “yyyyMMdd”        | Label with the days recorded in the first and |
|               |                   | last coordinate values.                       |
|---------------+-------------------+-----------------------------------------------|
| 6hr, 3hr,     | “yyyyMMddhhmm”    | Label 1hrCM files with the beginning of the   |
| 1hr,          |                   | first hour and the end of the last hour       |
| 1hrCM, 6hrPt, |                   | contributing to climatology (rounded to the   |
| 3hrPt,        |                   | nearest minute); for other frequencies in     |
| 1hrPt         |                   | this category, label with the first and last  |
|               |                   | time-coordinate values (rounded to the        |
|               |                   | nearest minute).                              |
|---------------+-------------------+-----------------------------------------------|
| subhrPt       | “yyyyMMddhhmmss”  | Label with the first and last time-coordinate |
|               |                   | values (rounded to the nearest second)        |
|---------------+-------------------+-----------------------------------------------|
| fx            | Omit time label   | This frequency applies to variables that are  |
|               |                   | independent of time (“fixed”).                |
|---------------+-------------------+-----------------------------------------------|

"""

import numpy as np
import pandas as pd
import pytest
import xarray as xr
from unittest.mock import Mock

from pymorize.files import (
    _filename_time_range,
    create_filepath,
    has_time_axis,
    is_datetime_type,
    needs_resampling,
    save_dataset,
    get_time_label,
)
from pymorize.timeaverage import _get_time_method

# Tests for time-span in filename


def test_no_timespan_in_filename_when_no_time_dim_in_data():
    ncells = 100
    ds = xr.DataArray(
        np.random.rand(ncells),
        dims=[
            "ncells",
        ],
        name="notime",
    )
    rule = {"frequency_str": "", "time_method": "INSTANTANEOUS"}
    expected = ""
    result = _filename_time_range(ds, rule)
    assert expected == result, f"Must be empty string. Got: {result}"


frequency_str = (
    "yr",
    "yrPt",
    "dec",
    "mon",
    "monC",
    "day",
    "6hr",
    "3hr",
    "1hr",
    "1hrCM",
    "6hrPt",
    "3hrPt",
    "1hrPt",
    "subhrPt",
    "fx",
)


@pytest.mark.parametrize("frequency", frequency_str)
def test__filename_time_range_allows_single_timestep(frequency):
    ds = xr.DataArray(
        np.random.random((1, 10)),
        coords={"time": pd.Timestamp("2020-01-02 10:10:10"), "ncells": list(range(10))},
        name="singleTS",
    )
    rule = {
        "frequency_str": frequency,
        "time_method": _get_time_method(frequency),
    }
    result = _filename_time_range(ds, rule)
    assert result == ""


@pytest.mark.parametrize("frequency", frequency_str)
def test__filename_time_range_multiple_timesteps(frequency):
    time = pd.date_range(
        "2020-01-01 15:12:13",
        "2021-01-01 06:15:17",
        freq="D",
    )
    ds = xr.DataArray(
        np.random.random((time.size, 2)),
        coords={
            "time": time,
            "ncells": [1, 2],
        },
        name="yeardata",
    )
    rule = {
        "frequency_str": frequency,
        "time_method": _get_time_method(frequency),
    }
    expected = {
        "yr": "2020-2020",
        "yrPt": "2020-2020",
        "dec": "2020-2020",
        "mon": "202001-202012",
        "monC": "202001-202012",
        "day": "20200101-20201231",
        "6hr": "202001011512-202012311512",
        "3hr": "202001011512-202012311512",
        "1hr": "202001011512-202012311512",
        "1hrCM": "202001011512-202012311512",
        "6hrPt": "202001011512-202012311512",
        "3hrPt": "202001011512-202012311512",
        "1hrPt": "202001011512-202012311512",
        "subhrPt": "20200101151213-20201231151213",
        "fx": "",
    }
    result = _filename_time_range(ds, rule)
    assert expected[frequency] == result


def test_no_resampling_required_when_data_timespan_is_less_than_target_timespan():
    t = pd.date_range("2020-01-01 1:00:00", "2020-02-28 1:00:00", freq="D")
    da = xr.DataArray(np.ones(t.size), coords={"time": t})
    timespan = "6ME"
    assert needs_resampling(da, timespan) is False


def test_needs_resampling_when_target_timespan_is_lower_than_data_timespan():
    t = pd.date_range("2020-01-01 1:00:00", "2020-02-28 1:00:00", freq="D")
    da = xr.DataArray(np.ones(t.size), coords={"time": t})
    timespan = "ME"
    assert needs_resampling(da, timespan) is True


def test_no_resampling_required_with_single_timestamp_data():
    da = xr.DataArray(10, coords={"time": pd.Timestamp.now()}, name="t")
    timespan = "1MS"
    assert needs_resampling(da, timespan) is False


def test_no_resampling_required_when_target_timespan_is_None():
    t = pd.date_range("2020-01-01 1:00:00", "2020-02-28 1:00:00", freq="D")
    da = xr.DataArray(np.ones(t.size), coords={"time": t})
    timespan = None
    assert needs_resampling(da, timespan) is False


def test_is_datetime_type_is_true_for_cftime():
    dates = xr.cftime_range(start="2001", periods=24, freq="MS", calendar="noleap")
    da_nl = xr.DataArray(np.arange(24), coords=[dates], dims=["time"], name="foo")
    assert is_datetime_type(da_nl.time.data) is True


def test_is_datetime_type_is_true_for_numpy_datetime64():
    t = pd.date_range("2020-01-01 1:00:00", periods=50, freq="6h")
    da = xr.DataArray(np.ones(t.size), coords={"time": t}, name="foo")
    assert is_datetime_type(da.time) is True


def test_has_time_axis_not_true_when_no_valid_time_dim_exists():
    da = xr.DataArray(
        10,
        coords={"time": 1},
        dims=[
            "time",
        ],
        name="notime",
    )
    assert has_time_axis(da) is False


def test_has_time_axis_is_true_with_time_as_scalar_coordinate():
    da = xr.DataArray(
        [10],
        coords={
            "time": (
                [
                    "time",
                ],
                [
                    pd.Timestamp.now(),
                ],
            )
        },
        name="t",
    )
    assert has_time_axis(da) is True


def test_has_time_axis_recognizes_T_as_time_dimension():
    t = pd.date_range("2020-01-01 1:00:00", periods=50, freq="6h")
    da = xr.DataArray(
        np.ones(t.size),
        coords={"T": t},
        dims=[
            "T",
        ],
        name="foo",
    )
    assert has_time_axis(da) is True


def test_get_time_label_can_recognize_time_dimension_named_time():
    np.random.seed(0)
    temperature = 15 + 8 * np.random.randn(2, 2, 3)
    lon = [[-99.83, -99.32], [-99.79, -99.23]]
    lat = [[42.25, 42.21], [42.63, 42.59]]
    time = pd.date_range("2014-09-06", periods=3)
    reference_time = pd.Timestamp("2014-09-05")
    da = xr.DataArray(
        data=temperature,
        dims=["x", "y", "time"],
        coords=dict(
            lon=(["x", "y"], lon),
            lat=(["x", "y"], lat),
            reference_time=reference_time,
            time=time,
        ),
        attrs=dict(
            description="Ambient temperature.",
            units="degC",
        ),
    )
    assert get_time_label(da) == "time"


def test_get_time_label_can_recognize_scalar_time_dimension():
    s = xr.DataArray(
        1,
        coords=dict(
            T=(
                [
                    "time",
                ],
                [pd.Timestamp.now()],
            )
        ),
        dims=[
            "time",
        ],
    )
    assert get_time_label(s) == "T"


def test_get_time_label_is_None_for_missing_time_dimension():
    np.random.seed(0)
    temperature = 15 + 8 * np.random.randn(2, 2, 3)
    lon = [[-99.83, -99.32], [-99.79, -99.23]]
    lat = [[42.25, 42.21], [42.63, 42.59]]
    time = pd.date_range("2014-09-06", periods=3)
    reference_time = pd.Timestamp("2014-09-05")
    da = xr.DataArray(
        data=temperature,
        dims=["x", "y", "time"],
        coords=dict(
            lon=(["x", "y"], lon),
            lat=(["x", "y"], lat),
            reference_time=reference_time,
            # Removing time dimension on purpose. get_time_label should not consider reference_time.
            # time=time,
        ),
        attrs=dict(
            description="Ambient temperature.",
            units="degC",
        ),
    )
    assert get_time_label(da) == None


def test_get_time_label_can_recognize_time_label_even_if_dimension_is_named_differently():
    b = xr.DataArray(
        [1, 2, 3],
        coords={
            "time": (
                [
                    "ncells",
                ],
                pd.date_range(pd.Timestamp.now(), periods=3, freq="h"),
            )
        },
        dims=[
            "ncells",
        ],
    )
    assert get_time_label(b) == "time"


def test_save_dataset_saves_to_single_file_when_no_time_axis(tmp_path):
    t = tmp_path / "output"
    da = xr.DataArray([1, 2, 3], coords={"ncells": [1, 2, 3]}, dims=["ncells"])
    rule = Mock()
    rule.data_request_variable.table.table_id = "Omon"
    rule.cmor_variable = "CO2"
    rule.variant_label = "r1i1p1f1"
    rule.source_id = "GFDL-ESM2M"
    rule.experiment_id = "historical"
    rule.output_directory = t
    # rule["institution"] = "AWI"
    # rule = {"frequency_str": "", "time_method": "INSTANTANEOUS"}
    save_dataset(da, rule)
