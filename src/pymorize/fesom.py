import numpy as np
import xarray as xr
from pyfesom2.load_mesh_data import load_mesh
from pyfesom2.regridding import fesom2regular

from .pipeline import FrozenPipeline


def attach_mesh_to_rule(data, rule):
    rule.mesh = load_mesh(rule.mesh_file)
    return data


def regrid_to_regular(data, rule):
    mesh = load_mesh(rule.mesh_file)
    box = rule.get("box", "-180, 180, -90, 90")
    x_min, x_max, y_min, y_max = map(float, box.split(","))
    x = np.linspace(x_min, x_max, int(x_max - x_min))
    y = np.linspace(y_min, y_max, int(y_max - y_min))
    lon, lat = np.meshgrid(x, y)
    interpolated = fesom2regular(data, mesh, lon, lat)
    return xr.DataArray(interpolated, coords=[("lon", lon), ("lat", lat)])


class FESOMRegridPipeline(FrozenPipeline):
    STEPS = ("pymorize.fesom.regrid_to_regular",)
    NAME = "pymorize.fesom.FESOMRegridPipeline"
