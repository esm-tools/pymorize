import xarray as xr
import re
from .rule import Rule


def setgrid(da: xr.Dataset | xr.DataArray, rule: Rule) -> xr.Dataset | xr.DataArray:
    """
    Appends grid information to data file if necessary coordinate dimensions exits in data file.
    Renames dimensions in data file to match the dimension names in grid file if necessary.

    Parameters
    ----------
    da : xr.DataSet or xr.DataArray
        The input dataarray or dataset.
    rule: Rule object containing gridfile attribute

    Returns
    -------
    xr.DataSet
        The output dataarray or dataset with the grid information.
    """
    gridfile = rule.get("grid_file")
    if gridfile is None:
        raise ValueError("Missing grid file. Please set 'grid_file' in the rule.")
    grid = xr.open_dataset(gridfile)
    required_dims = set(sum([gc.dims for _, gc in grid.coords.items()], ()))
    to_rename = {}
    can_merge = False
    for dim in required_dims:
        dimsize = grid.sizes[dim]
        if dim in da.sizes:
            can_merge = True
            if da.sizes[dim] != dimsize:
                raise ValueError(
                    f"Mismatch dimension sizes {dim} {dimsize} (grid) {da.sizes[dim]} (data)"
                )
        else:
            for name, _size in da.sizes.items():
                if dimsize == _size:
                    can_merge = True
                    to_rename[name] = dim
    if can_merge:
        if to_rename:
            da = da.rename_dims(to_rename)
        coord_names = "|".join(grid.coords.keys())
        pattern = re.compile(f"({coord_names}).+")
        required_vars = [name for name in grid.variables.keys() if pattern.match(name)]
        new_grid = grid[required_vars]
        da = new_grid.merge(da)
    return da
