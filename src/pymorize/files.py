"""
This module contains functions for handling file-related operations in the pymorize package.
It includes functions for creating filepaths based on given rules and datasets, and for
saving the resulting datasets to the generated filepaths.
"""

import xarray as xr


def create_filepath(ds, rule):
    """
    Generate a filepath when given an xarray dataset and a rule.

    This function generates a filepath for the output file based on the given dataset and rule.
    The filepath includes the name, table_id, institution, source_id, experiment_id, label, grid, and optionally the start and end time.

    Parameters
    ----------
    ds : xarray.Dataset
        The input dataset.
    rule : Rule
        The rule object containing information for generating the filepath.

    Returns
    -------
    str
        The generated filepath.

    Notes
    -----
    The rule object should have the following attributes: cmor_variable, data_request_variable, variant_label, source_id, experiment_id, output_directory, and optionally institution.
    """
    name = rule.cmor_variable
    table_id = rule.data_request_variable.table.table_id  # Omon
    label = rule.variant_label  # r1i1p1f1
    source_id = rule.source_id  # AWI-CM-1-1-MR
    experiment_id = rule.experiment_id  # historical
    out_dir = rule.output_directory  # where to save output files
    institution = rule.get("institution", "AWI")
    grid = "gn"  # grid_type
    if "time" in ds.dims:
        start = ds.time.data[0].strftime("%Y%m")
        end = ds.time.data[-1].strftime("%Y%m")
        filepath = f"{out_dir}/{name}_{table_id}_{institution}-{source_id}_{experiment_id}_{label}_{grid}_{start}-{end}.nc"
    else:
        filepath = f"{out_dir}/{name}_{table_id}_{institution}-{source_id}_{experiment_id}_{label}_{grid}.nc"
    return filepath


def save_dataset(da: xr.DataArray, rule):
    """
    save datasets to multiple files

    NOTE: prior to calling this function, call dask.compute() method,
    otherwise tasks will progress very slow.
    """
    file_timespan = rule.file_timespan
    if "time" not in da.dims:
        filepath = create_filepath(da, rule)
        return da.to_netcdf(filepath, mode="w", format="NETCDF4")
    if isinstance(da, xr.DataArray):
        da = da.to_dataset()
    frequency_str = frequency_from_approx_interval(file_timespan)
    groups = da.resample(time=frequency_str)
    paths = []
    datasets = []
    for group_name, group_ds in groups:
        paths.append(create_filepath(group_ds, rule))
        datasets.append(group_ds)
    return xr.save_mfdataset(datasets, paths)
