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


def test__split_by_chunks_empty_dataarray():
    da = xr.DataArray()
    result = pymorize.timeaverage._split_by_chunks(da)
