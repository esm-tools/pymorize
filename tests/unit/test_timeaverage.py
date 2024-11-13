import numpy as np
import pandas as pd
import pytest
import xarray as xr

import pymorize.timeaverage

TABLE_TIME_METHOD = {
    "CMIP6_3hr": "MEAN",
    "CMIP6_6hrLev": "MEAN",
    "CMIP6_6hrPlev": "MEAN",
    "CMIP6_6hrPlevPt": "INSTANTANEOUS",
    "CMIP6_AERday": "MEAN",
    "CMIP6_AERhr": "MEAN",
    "CMIP6_AERmon": "MEAN",
    "CMIP6_AERmonZ": "MEAN",
    "CMIP6_Amon": "MEAN",
    "CMIP6_CF3hr": "MEAN",
    "CMIP6_CFday": "MEAN",
    "CMIP6_CFmon": "MEAN",
    "CMIP6_CFsubhr": "MEAN",
    "CMIP6_CV": "MEAN",
    "CMIP6_E1hr": "MEAN",
    "CMIP6_E1hrClimMon": "CLIMATOLOGY",
    "CMIP6_E3hr": "MEAN",
    "CMIP6_E3hrPt": "INSTANTANEOUS",
    "CMIP6_E6hrZ": "MEAN",
    "CMIP6_Eday": "MEAN",
    "CMIP6_EdayZ": "MEAN",
    "CMIP6_Efx": "MEAN",
    "CMIP6_Emon": "MEAN",
    "CMIP6_EmonZ": "MEAN",
    "CMIP6_Esubhr": "MEAN",
    "CMIP6_Eyr": "MEAN",
    "CMIP6_IfxAnt": "MEAN",
    "CMIP6_IfxGre": "MEAN",
    "CMIP6_ImonAnt": "MEAN",
    "CMIP6_ImonGre": "MEAN",
    "CMIP6_IyrAnt": "MEAN",
    "CMIP6_IyrGre": "MEAN",
    "CMIP6_LImon": "MEAN",
    "CMIP6_Lmon": "MEAN",
    "CMIP6_Oclim": "CLIMATOLOGY",
    "CMIP6_Oday": "MEAN",
    "CMIP6_Odec": "MEAN",
    "CMIP6_Ofx": "MEAN",
    "CMIP6_Omon": "MEAN",
    "CMIP6_Oyr": "MEAN",
    "CMIP6_SIday": "MEAN",
    "CMIP6_SImon": "MEAN",
    "CMIP6_coordinate": "MEAN",
    "CMIP6_day": "MEAN",
    "CMIP6_formula_terms": "MEAN",
    "CMIP6_fx": "MEAN",
    "CMIP6_grids": "MEAN",
    "CMIP6_input_example": "MEAN",
}


@pytest.mark.parametrize("table_name, expected", TABLE_TIME_METHOD.items())
def test__get_time_method(table_name, expected):
    answer = pymorize.timeaverage._get_time_method(table_name)
    assert answer == expected


def test__split_by_chunks_1d():
    # 1D array with chunks
    data = xr.DataArray(np.arange(10), dims="x").chunk({"x": 5})
    chunks = list(pymorize.timeaverage._split_by_chunks(data))
    assert len(chunks) == 2  # Expecting 2 chunks for x dimension
    assert chunks[0][0] == {"x": slice(0, 5)}
    assert chunks[1][0] == {"x": slice(5, 10)}


def test__split_by_chunks_2d():
    # 2D array with chunks
    data = xr.DataArray(np.arange(100).reshape(10, 10), dims=("x", "y")).chunk(
        {"x": 5, "y": 2}
    )
    chunks = list(pymorize.timeaverage._split_by_chunks(data))
    assert len(chunks) == 10  # Expecting 10 chunks (5 for x, 2 for y)
    assert chunks[0][0] == {"x": slice(0, 5), "y": slice(0, 2)}
    assert chunks[-1][0] == {"x": slice(5, 10), "y": slice(8, 10)}


def test__split_by_chunks_no_chunks():
    # Unchunked data should raise an informative error or handle gracefully
    data = xr.DataArray(np.arange(10), dims="x")
    # Split-by-chunks is meaningless if you have no chunks, so you should...
    # ...get back the same data?
    # assert data == pymorize.timeaverage._split_by_chunks(data)
    # or
    # ...get an error?
    with pytest.raises(TypeError):
        list(pymorize.timeaverage._split_by_chunks(data))


def test__split_by_chunks_fesom_single_timestep(pi_uxarray_data):
    ds = xr.open_mfdataset(
        f for f in pi_uxarray_data.iterdir() if f.name.startswith("temp")
    )
    chunks = list(pymorize.timeaverage._split_by_chunks(ds))
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
    chunks = list(pymorize.timeaverage._split_by_chunks(ds))
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
        pymorize.timeaverage._frequency_from_approx_interval("3650") == "10YE"
    )  # Decade conversion


def test__frequency_from_approx_interval_year():
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("365") == "YE"
    )  # One year
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("1095") == "3YE"
    )  # Three years


def test__frequency_from_approx_interval_month():
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("30") == "ME"
    )  # One month
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("60") == "2ME"
    )  # Two months


def test__frequency_from_approx_interval_day():
    assert pymorize.timeaverage._frequency_from_approx_interval("1") == "D"  # One day


def test__frequency_from_approx_interval_hour():
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.04167") == "H"
    )  # Approximately one hour in days
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.08334") == "2H"
    )  # Approximately two hours in days
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.5") == "12H"
    )  # Half a day in hours


def test__frequency_from_approx_interval_minute():
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.000694") == "min"
    )  # Approximately one minute in days
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.001388") == "2min"
    )  # Approximately two minutes in days
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.020833") == "30min"
    )  # Approximately half an hour in minutes


def test__frequency_from_approx_interval_second():
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.00001157") == "s"
    )  # Approximately one second in days
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("0.00002314") == "2s"
    )  # Approximately two seconds in days
    assert not (
        pymorize.timeaverage._frequency_from_approx_interval("0.000694") == "60s"
    )  # Approximately one minute in seconds, should give back min, since it can round up.


def test__frequency_from_approx_interval_millisecond():
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("1.1574e-8") == "ms"
    )  # Approximately one millisecond in days
    assert (
        pymorize.timeaverage._frequency_from_approx_interval("2.3148e-8") == "2ms"
    )  # Approximately two milliseconds in days


def test__invalid_interval():
    with pytest.raises(ValueError):
        pymorize.timeaverage._frequency_from_approx_interval("not_a_number")


def test__compute_file_timespan_single_chunk():
    # Create a DataArray with a single chunk
    time = pd.date_range("2000-01-01", periods=10, freq="D")
    data = xr.DataArray(np.random.rand(10), dims="time", coords={"time": time})
    data = data.chunk({"time": 5})  # Single chunk

    assert pymorize.timeaverage._compute_file_timespan(data) == 9


def test__compute_file_timespan_multiple_chunks():
    # Create a DataArray with multiple chunks
    time = pd.date_range("2000-01-01", periods=30, freq="D")
    data = xr.DataArray(np.random.rand(30), dims="time", coords={"time": time})
    data = data.chunk({"time": 10})

    assert pymorize.timeaverage._compute_file_timespan(data) == 9


def test__compute_file_timespan_empty_time_dimension():
    # DataArray with an empty time dimension
    data = xr.DataArray(np.array([]), dims="time", coords={"time": []})
    with pytest.raises(ValueError, match="no time values in this chunk"):
        pymorize.timeaverage._compute_file_timespan(data)


def test__compute_file_timespan_missing_time_dimension():
    # DataArray without a time dimension
    data = xr.DataArray(np.random.rand(10), dims="x")
    with pytest.raises(ValueError, match="missing the 'time' dimension"):
        pymorize.timeaverage._compute_file_timespan(data)


def test__compute_file_timespan_non_sequential_time():
    # DataArray with non-sequential time points
    time = pd.to_datetime(["2000-01-01", "2000-01-05", "2000-01-20", "2000-01-30"])
    data = xr.DataArray(np.random.rand(4), dims="time", coords={"time": time})
    data = data.chunk({"time": 2})

    assert pymorize.timeaverage._compute_file_timespan(data) == 29


def test__compute_file_timespan_large_dataarray():
    # DataArray with a larger number of chunks
    time = pd.date_range("2000-01-01", periods=100, freq="D")
    data = xr.DataArray(np.random.rand(100), dims="time", coords={"time": time})
    data = data.chunk({"time": 20})

    assert pymorize.timeaverage._compute_file_timespan(data) == 19
