"""
Set grid information on the data file.

xarray does not have a built-in `setgrid` operator unlike `cdo`.  Using
`xarray.merge` directly to merge grid with data may or may not produce the
desired result all the time.

Some guiding rules to set the grid information:

1. At least one dimension size in both data file and grid file should match.
2. If the dimension size match but not the dimension name, then the dimension
   name in data file is renamed to match the dimension name in grid file.
3. The matching dimension size must be one of the coordinate variables in both data
   file and grid file.
4. If all above conditions are met, then the data file is merged with the grid file.
5. The data variables which are prefixed with coordinate variables in the grid file
   are kept and the rest of the data variables in grid file are dropped.
6. The result of the merge is always a xarray.Dataset

Note: Rule 5 is not strict and may go away if it is not desired.
"""

import re
from typing import Union

import xarray as xr

from ..core.logging import logger
from ..core.rule import Rule


def setgrid(
    da: Union[xr.Dataset, xr.DataArray], rule: Rule
) -> Union[xr.Dataset, xr.DataArray]:
    """
    Appends grid information to data file if necessary coordinate dimensions exits in data file.
    Renames dimensions in data file to match the dimension names in grid file if necessary.

    Parameters
    ----------
    da : xr.Dataset or xr.DataArray
        The input dataarray or dataset.
    rule: Rule object containing gridfile attribute

    Returns
    -------
    xr.Dataset
        The output dataarray or dataset with the grid information.
    """
    logger.info("Starting setgrid step")
    gridfile = rule.get("grid_file")
    logger.info(f"    * Using {gridfile=}")
    if gridfile is None:
        raise ValueError("Missing grid file. Please set 'grid_file' in the rule.")
    grid = xr.open_dataset(gridfile)
    required_dims = set(sum([gc.dims for _, gc in grid.coords.items()], ()))
    logger.info(f"    * Determined required_dims as {required_dims=}")
    to_rename = {}
    can_merge = False
    for dim in required_dims:
        dimsize = grid.sizes[dim]
        logger.info(f"Checking if {dim=} is in {da.sizes=}")
        if dim in da.sizes:
            can_merge = True
            if da.sizes[dim] != dimsize:
                raise ValueError(
                    f"Mismatch dimension sizes {dim} {dimsize} (grid) {da.sizes[dim]} (data)"
                )
        else:
            logger.info(f"{dim=} is not in {da.sizes=}")
            logger.info("Need to check individual sizes...")
            for name, _size in da.sizes.items():
                logger.info(f"{name=}, {_size=}")
                if dimsize == _size:
                    can_merge = True
                    to_rename[name] = dim
    logger.info(f"    * After inspection, {can_merge=}")
    if can_merge:
        if to_rename:
            da = da.rename(to_rename)
        coord_names = "|".join(grid.coords.keys())
        pattern = re.compile(f"({coord_names}).+")
        required_vars = [name for name in grid.variables.keys() if pattern.match(name)]
        new_grid = grid[required_vars]
        da = new_grid.merge(da)
    else:
        logger.warning(
            "!!! SETGRID Step was requested by nothing to be merged! Check carefully!"
        )
    return da
