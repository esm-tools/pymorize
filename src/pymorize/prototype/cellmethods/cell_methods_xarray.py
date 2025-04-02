from typing import List, Optional, Tuple

import numpy as np
import xarray as xr

from .cellmethods_parser import parse_cell_methods

"""
Prototype code only. Not sure if cellmethods are handled this way. Lot of ambiguity at many steps.
"""


class CellMethodsConverter:
    def __init__(self):
        self.function_map = {
            "mean": xr.DataArray.mean,
            "sum": xr.DataArray.sum,
            "maximum": xr.DataArray.max,
            "minimum": xr.DataArray.min,
            "point": lambda x, dim: x.isel(**{dim: 0}),
        }

        self.dimension_map = {
            "area": "area",
            "time": "time",
            "depth": "depth",
            "longitude": "lon",
            "grid_longitude": "grid_lon",
        }

    def apply_constraint(
        self, da: xr.DataArray, constraint: str, value: str, scope: Optional[str] = None
    ) -> xr.DataArray:
        """Apply where/over constraints to the DataArray."""
        if constraint == "where":
            # Handle special cases with mask variables
            if scope and "(comment: mask=" in scope:
                mask_var = scope.split("mask=")[1].rstrip(")")
                # Assuming the mask variable is available in the same dataset
                return da.where(da.coords[mask_var] > 0)

            # Handle basic area type constraints
            area_types = [
                "land",
                "sea",
                "ice_sheet",
                "sea_ice",
                "crops",
                "trees",
                "vegetation",
                "unfrozen_soil",
                "cloud",
                "natural_grasses",
                "floating_ice_shelf",
                "grounded_ice_sheet",
                "ice_free_sea",
                "sea_ice_melt_pond",
                "sea_ice_ridges",
                "snow",
                "sector",
                "shrubs",
                "pastures",
            ]

            if value in area_types:
                # Use the mask from coordinates
                mask_var = f"{value}_mask"
                mask = da.coords[mask_var]
                # Create a boolean mask array that matches the data dimensions
                mask_data = mask.values > 0
                # Broadcast mask to match data dimensions
                for _ in range(len(da.dims) - 1):
                    mask_data = mask_data[:, np.newaxis]
                # Apply the mask
                return da.where(mask_data)

        elif constraint == "over":
            if value == "all_area_types":
                # No filtering needed, already considering all areas
                return da
            elif value in ["days", "months", "years", "hours"]:
                # This will be handled in the time aggregation
                return da

        return da

    def process_cell_method(
        self, da: xr.DataArray, method: List[Tuple[str, str]]
    ) -> xr.DataArray:
        """Process a single cell method (one group of operations)."""
        result = da.copy()  # Make a copy to preserve coordinates
        dim = None
        func = None
        constraints = []
        scope = None

        for token_type, token_value in method:
            if token_type == "DIMENSION":
                dim = self.dimension_map.get(token_value, token_value)
            elif token_type == "FUNCTION":
                func = self.function_map[token_value]
            elif token_type == "CONSTRAINT":
                constraints.append(token_value)
            elif token_type == "AREATYPE" or token_type == "SELECTION":
                if constraints:
                    result = self.apply_constraint(
                        result, constraints[-1], token_value, scope
                    )
            elif token_type == "SCOPE":
                scope = token_value

        if dim and func:
            # Handle time-based selections before applying the function
            if dim == "time" and constraints and constraints[-1] == "over":
                # Get the appropriate time frequency
                freq = {"hours": "h", "days": "D", "months": "M", "years": "Y"}.get(
                    token_value
                )
                if freq:
                    result = result.resample(time=freq).mean()
            else:
                # Apply the main function
                if func == self.function_map["point"]:
                    result = result.isel(**{dim: 0})
                else:
                    result = func(result, dim=dim)

        return result

    def apply_cell_methods(
        self, da: xr.DataArray, cell_methods_str: str
    ) -> xr.DataArray:
        """Apply cell methods to a DataArray based on the cell_methods string."""
        parsed = parse_cell_methods(cell_methods_str)
        if parsed is None:
            raise ValueError(f"Failed to parse cell methods string: {cell_methods_str}")

        result = da
        for method in parsed:
            result = self.process_cell_method(result, method)

        return result


# Example usage:
def apply_cell_methods(da: xr.DataArray, cell_methods_str: str) -> xr.DataArray:
    """
    Apply cell methods to a DataArray based on the cell_methods string.

    Args:
        da: Input xarray DataArray
        cell_methods_str: Cell methods string (e.g., "area: mean time: maximum")

    Returns:
        Processed xarray DataArray

    Example:
        >>> import xarray as xr
        >>> import numpy as np
        >>> data = np.random.rand(4, 3, 2)  # time, area, depth
        >>> da = xr.DataArray(data, dims=['time', 'area', 'depth'])
        >>> result = apply_cell_methods(da, "area: mean time: maximum")
    """
    converter = CellMethodsConverter()
    return converter.apply_cell_methods(da, cell_methods_str)
