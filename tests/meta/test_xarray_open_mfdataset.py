import xarray as xr


def test_open_fesom_2p6_pimesh_esm_tools(fesom_2p6_pimesh_esm_tools_data):
    ds = xr.open_mfdataset(
        f
        for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
        if f.name.startswith("temp")
    )
    print(ds)
