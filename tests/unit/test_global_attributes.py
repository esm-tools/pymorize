import pytest
import xarray as xr

from pymorize.global_attributes import set_global_attributes

# Name, expected pass
required_attributes = {
    ("activity_id", True),
    ("Conventions", True),
    ("creation_date", True),
    ("data_specs_version", True),
    ("experiment", True),
    ("experiment_id", True),
    ("forcing_index", True),
    ("frequency", True),
    ("further_info_url", True),
    ("grid", True),
    ("grid_label", True),
    ("initialization_index", True),
    ("institution", True),
    ("institution_id", True),
    ("license", True),
    ("mip_era", True),
    ("nominal_resolution", True),
    ("physics_index", True),
    ("product", True),
    ("realization_index", True),
    ("realm", True),
    ("source", True),
    ("source_id", True),
    ("source_type", True),
    ("sub_experiment", True),
    ("sub_experiment_id", True),
    ("table_id", True),
    ("tracking_id", False),
    ("variable_id", True),
    ("variant_label", True),
}


@pytest.mark.parametrize("added_attributes, expected_pass", required_attributes)
def test_global_attributes_has_expected_attributes(
    pi_uxarray_temp_rule, pi_uxarray_data, added_attributes, expected_pass
):
    if not expected_pass:
        pytest.xfail(f"Test should fail with attribute {added_attributes}")
    matching_files = [
        f for f in (pi_uxarray_data).iterdir() if f.name.startswith("temp.fesom")
    ]
    ds = xr.open_mfdataset(
        matching_files,
        engine="h5netcdf",
    )
    ds_out = set_global_attributes(ds, pi_uxarray_temp_rule)
    assert added_attributes in ds_out.attrs
