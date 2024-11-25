import xarray as xr

from pymorize.fesom_1p4 import load_mesh_data, nodes_to_levels


def test_nodes_to_levels_with_awicm_1p0_recom_data(awicm_1p0_recom_data):
    outdata_path_stub = "awi-esm-1-1-lr_kh800/piControl/outdata/fesom/"
    outdata_files = sorted(list((awicm_1p0_recom_data / outdata_path_stub).iterdir()))
    # NOTE(PG): Just check the first file, for this test
    ds = xr.open_mfdataset(outdata_files).thetao
    mesh = load_mesh_data.load_mesh(
        f"{awicm_1p0_recom_data}/awi-esm-1-1-lr_kh800/piControl/input/fesom/mesh/"
    )
    indices = nodes_to_levels.indicies_from_mesh(mesh)
    ds_out = nodes_to_levels.interpolate_dataarray(ds, mesh, indices)
    # NOTE(PG): For now, just check if the output object is created
    # FIXME(PG): Correctness check...
    assert ds_out is not None
