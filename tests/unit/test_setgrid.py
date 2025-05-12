import cftime
import numpy as np
import xarray as xr

from pymor.std_lib.setgrid import setgrid


def test_open_dataset_can_read_fake_grid(fake_grid_file):
    grid = xr.open_dataset(fake_grid_file)
    assert "ncells" in grid.sizes
    assert "lon" in grid.coords
    assert "lat" in grid.coords
    assert "lon_bnds" in grid.data_vars
    assert "lat_bnds" in grid.data_vars
    assert "cell_area" in grid.data_vars
    assert "node_node_links" in grid.data_vars
    assert "triag_nodes" in grid.data_vars
    assert "coast" in grid.data_vars
    assert "depth" in grid.data_vars
    assert "depth_lev" in grid.data_vars
    grid.close()


def test_sets_grid_on_dataset(fake_grid_file):
    rule = {"grid_file": str(fake_grid_file)}
    ncells = 100
    ntimesteps = 10
    t = range(84600, 84600 * (ntimesteps + 1), 84600)
    time = cftime.num2date(t, units="seconds since 2686-01-01", calendar="standard")
    da = xr.DataArray(
        np.random.rand(ntimesteps, ncells),
        dims=["time", "ncells"],
        coords={"time": time},
        name="CO2",
    )
    new_da = setgrid(da, rule)
    assert "ncells" in new_da.sizes
    assert "time" in new_da.sizes
    assert "time" in new_da.coords
    assert "lon" in new_da.coords
    assert "lat" in new_da.coords
    assert "lon_bnds" in new_da.data_vars
    assert "lat_bnds" in new_da.data_vars
    # setgrid will skip setting the following variables (cdo also skips these)
    assert "cell_area" not in new_da.data_vars
    assert "node_node_links" not in new_da.data_vars
    assert "triag_nodes" not in new_da.data_vars
    assert "coast" not in new_da.data_vars
    assert "depth" not in new_da.data_vars
    assert "depth_lev" not in new_da.data_vars


def test_renaming_data_dimension_to_match_dimension_in_grid(fake_grid_file):
    rule = {"grid_file": str(fake_grid_file)}
    nodes_2d = 100
    ntimesteps = 10
    t = range(84600, 84600 * (ntimesteps + 1), 84600)
    time = cftime.num2date(t, units="seconds since 2686-01-01", calendar="standard")
    da = xr.DataArray(
        np.random.rand(ntimesteps, nodes_2d),
        dims=["time", "nodes_2d"],
        coords={"time": time},
        name="CO2",
    )
    new_da = setgrid(da, rule)
    assert "nodes_2d" not in new_da.sizes
    assert "nodes_2d" not in new_da.coords
    assert "ncells" in new_da.sizes


def test_skip_grid_setting_if_no_matching_dimension_in_data_is_found(fake_grid_file):
    rule = {"grid_file": str(fake_grid_file)}
    nodes_2d = 50
    ntimesteps = 10
    t = range(84600, 84600 * (ntimesteps + 1), 84600)
    time = cftime.num2date(t, units="seconds since 2686-01-01", calendar="standard")
    da = xr.DataArray(
        np.random.rand(ntimesteps, nodes_2d),
        dims=["time", "nodes_2d"],
        coords={"time": time},
        name="CO2",
    )
    new_da = setgrid(da, rule)
    assert "ncells" not in new_da.sizes
    assert "lat" not in new_da.coords
    assert "lon" not in new_da.coords
    assert "lon_bnds" not in new_da.coords
    assert "lat_bnds" not in new_da.coords
