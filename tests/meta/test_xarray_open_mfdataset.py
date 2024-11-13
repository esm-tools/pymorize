import xarray as xr


def test_open_fesom_2p6_pimesh_esm_tools(fesom_2p6_pimesh_esm_tools_data):
    matching_files = [
        f
        for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
        if f.name.startswith("temp.fesom")
    ]
    assert len(matching_files) > 0
    print(matching_files)
    ds = xr.open_mfdataset(matching_files)
    print(ds)
