# Just import dask for parallelisms...
import dask  # noqa
import pytest
import xarray as xr


@pytest.mark.parametrize("engine", ["netcdf4", "h5netcdf"])
def test_open_fesom_2p6_pimesh_esm_tools(fesom_2p6_pimesh_esm_tools_data, engine):
    ds = xr.open_mfdataset(
        (
            f
            for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
            if f.name.startswith("temp")
        ),
        engine=engine,
    )
    assert isinstance(ds, xr.Dataset)


@pytest.mark.parametrize("engine", ["netcdf4", "h5netcdf"])
def test_open_fesom_2p6_pimesh_esm_tools_cftime(
    fesom_2p6_pimesh_esm_tools_data, engine
):
    ds = xr.open_mfdataset(
        (
            f
            for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
            if f.name.startswith("temp")
        ),
        use_cftime=True,
        engine=engine,
    )
    assert isinstance(ds, xr.Dataset)


@pytest.mark.parametrize("engine", ["netcdf4", "h5netcdf"])
def test_open_fesom_2p6_pimesh_esm_tools_parallel(
    fesom_2p6_pimesh_esm_tools_data, engine
):
    ds = xr.open_mfdataset(
        (
            f
            for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
            if f.name.startswith("temp")
        ),
        parallel=True,
        engine=engine,
    )
    assert isinstance(ds, xr.Dataset)


@pytest.mark.parametrize("engine", ["netcdf4", "h5netcdf"])
def test_open_fesom_2p6_pimesh_esm_tools_full(fesom_2p6_pimesh_esm_tools_data, engine):
    ds = xr.open_mfdataset(
        (
            f
            for f in (fesom_2p6_pimesh_esm_tools_data / "outdata/fesom/").iterdir()
            if f.name.startswith("temp")
        ),
        use_cftime=True,
        parallel=True,
        engine=engine,
    )
    assert isinstance(ds, xr.Dataset)
