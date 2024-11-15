import xarray as xr


def test_open_fesom_2p6_pimesh_esm_tools(fesom_2p6_pimesh_esm_tools_data):
    ds = xr.open_mfdataset(
        f
        for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
        if f.name.startswith("temp")
    )
    assert isinstance(ds, xr.Dataset)


def test_open_fesom_2p6_pimesh_esm_tools_parallel(fesom_2p6_pimesh_esm_tools_data):
    ds = xr.open_mfdataset(
        f
        for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
        if f.name.startswith("temp"),
        parallel=True,
    )
    assert isinstance(ds, xr.Dataset)

def test_open_fesom_2p6_pimesh_esm_tools_cftime(fesom_2p6_pimesh_esm_tools_data):
    ds = xr.open_mfdataset(
        f
        for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
        if f.name.startswith("temp"),
        use_cftime=True,
    )
    assert isinstance(ds, xr.Dataset)

def test_open_fesom_2p6_pimesh_esm_tools_full(fesom_2p6_pimesh_esm_tools_data):
    ds = xr.open_mfdataset(
        f
        for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
        if f.name.startswith("temp"),
        use_cftime=True,
        parallel=True,
    )
    assert isinstance(ds, xr.Dataset)
