import numpy as np
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
