import numpy as np
import xarray as xr

from pymorize.data_request import DataRequestVariable
from pymorize.rule import Rule
from pymorize.units import handle_unit_conversion


def test_units_with_psu():
    da = xr.DataArray(10, name="sos", attrs={"units": "psu"})
    rule = Rule(
        cmor_variable="sos",
        dimensionless_unit_mappings={"sos": {"0.001": "g/kg"}},
    )
    drv = DataRequestVariable(
        variable_id="sos",
        unit="0.001",
        description="Salinity of the ocean",
        time_method="MEAN",
        table="Omon",
        frequency="Monthly",
        realms="Ocean",
        standard_name="salinity_ocean",
        cell_methods="area: mean where sea",
        cell_measures="area: areacello",
    )
    rule.data_request_variable = drv
    new_da = handle_unit_conversion(da, rule)
    assert new_da.attrs.get("units") == "0.001"
    # Check the magnitude of the data
    # 1 g/kg is approximately 1 psu, so the values should be 10 * 1000
    # after conversion:
    assert np.allclose(new_da.values, 10000)
