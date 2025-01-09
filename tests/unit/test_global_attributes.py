import pytest

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
    # ("further_info_url", True),  # set on license, not explicitly req.
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
    # ("sub_experiment", False),  # need to figure this out
    ("sub_experiment_id", True),
    ("table_id", True),
    ("tracking_id", False),
    ("variable_id", True),
    ("variant_label", True),
}

"""
@pytest.mark.parametrize("added_attributes, expected_pass", required_attributes)
def test_global_attributes_has_expected_attributes(
    pi_uxarray_temp_rule, dr_sos, pi_uxarray_data, added_attributes, expected_pass
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
    test_rule = pi_uxarray_temp_rule
    test_rule.data_request_variable = dr_sos
    ds_out = set_global_attributes(ds, test_rule)
    assert added_attributes in ds_out.attrs
"""


@pytest.mark.parametrize("added_attributes, expected_pass", required_attributes)
def test_global_attributes_has_expected_attributes(added_attributes, expected_pass):
    class Fake:
        pass

    ds = Fake()
    ds.attrs = {}
    rule = Fake()
    table_header = Fake()
    drv = Fake()
    header = {
        "table_id": "Omon",
        "mip_era": "CMIP6",
        "realm": "ocnBgchem",
        "Conventions": "CF-1.7 CMIP-6.2",
        "product": "model-output",
        "data_specs_version": "01.00.33",
    }
    for name, val in header.items():
        setattr(table_header, name, val)

    drv.frequency = "mon"
    drv.table_header = table_header
    rule.data_request_variable = drv
    rule.cmor_variable = "fgco2"
    rule.variant_label = "r1i1p1f1"
    rule.source_id = "AWI-CM-1-1-MR"
    rule.experiment_id = "1pctCO2"
    rule.model_component = "atmos"
    rule.grid_label = "gn"
    ds_out = set_global_attributes(ds, rule)
    assert added_attributes in ds_out.attrs
