# timeaverage.py


import xarray as xr
import flox
import flox.xarray  # noqa: F401
import pandas as pd  # noqa: F401
import itertools


"""
The approximate_interval for time averaging is prescribed in the cmor tables.

In each table header approx_interval is provided. This information is also
provided in frequency.py
"""


def monthly_mean(da: xr.DataArray):
    """Monthly means per year.

    In usual pratice, da.groupby('time.month').mean("time") does monthly means
    over multiple years.  For instance, doing a monthly mean on a 5 year dataset
    results in collapsing all years to 12 months (12 timesteps).  This function
    preserves years, i.e., a 5 year dataset * 12 months => 60 timesteps.
    """
    t = da.resample(time="ME").mean("time")
    return t


def split_by_chunks(dataset: xr.DataArray):
    """splitting large data into sub-datasets for each chunk
    https://github.com/pydata/xarray/issues/1093#issuecomment-259213382
    """
    chunk_slices = {}
    for dim, chunks in dataset.chunks.items():
        slices = []
        start = 0
        for chunk in chunks:
            stop = start + chunk
            slices.append(slice(start, stop))
            start = stop
        chunk_slices[dim] = slices
    for slices in itertools.product(*chunk_slices.values()):
        selection = dict(zip(chunk_slices.keys(), slices))
        yield (selection, dataset[selection])


def get_time_method(table_id: str) -> str:
    if table_id.endswith("Pt"):
        return "INSTANTANEOUS"
    if table_id.endswith("C") or table_id.endswith("CM"):
        return "CLIMATOLOGY"
    return "MEAN"


def timeavg(da: xr.DataArray, rule):
    """Time averages data with respect to time-method (mean/climotolgy/instant.)"""
    # TODO: refactor file_timespan to a seperate function
    # before time-averaging figure out the timespan in a file
    #
    # the following has a edge case when the first check does not
    # realize the full extent of the time span
    # example: netcdf file representing a year span of data may start
    # in the middle of the year
    #
    # for selection, subset in split_by_chunks(da):
    #     break
    #
    # considering first few chunks
    chunks = split_by_chunks(da)
    tmp_file_timespan = []
    for i in range(3):
        try:
            subset = next(chunks)
        except StopIteration:
            pass
        else:
            tmp_file_timespan.append((subset.time.data[-1] - subset.time.data[0]).days)
    file_timespan = max(tmp_file_timespan)

    # time-averaging part
    rule.file_timespan = file_timespan
    drv = rule.data_request_variable
    approx_interval = f"{float(drv.table.approx_interval)}D"
    timemethod = get_time_method(drv.table.table_id)
    if timemethod == "INSTANTANEOUS":
        ds = da.resample(time=approx_interval).first()
    elif timemethod == "MEAN":
        ds = da.resample(time=approx_interval).mean()
        adjust_timestamp = rule.get("adjust_timestamp", True)
        if adjust_timestamp:
            approx_interval = rule.table.approx_interval
            # approx_interval is express in Days
            # (30 days to represent a month, 0.125 days for 3hr)
            # convert days to hours. offset is half of the interval
            offset = pd.offsets.Hour(float(approx_interval) * 24 / 2)
            ds["time"] = ds.time.to_pandas() + offset
    else:
        # CLIMATOLOGY
        if drv.table.frequency == "monC":
            ds = da.groupby("time.month").mean("time")
        elif drv.table.frequency == "1hrCM":
            ds = da.groupby("time.hour").mean("time")
        else:
            raise ValueError(
                f"Unknown Climatology {drv.table.frequency} in Table {drv.table.table_id}"
            )
    return ds


def create_filepath(ds, rule):
    """Generate a filepath when given an xarray dataset
    Parameters
    ----------
    ds: xarray dataset
    prefix : prefix of the output file name
    root_path : path to the output file. Defaults to current directory
    """
    name = rule.cmor_varialbe
    table_id = rule.table.table_id  # Omon
    label = rule.variant_label  # r1i1p1f1
    source_id = rule.source_id  # AWI-CM-1-1-MR
    experiment_id = rule.experiment_id  # historical
    out_dir = rule.out_dir  # where to save output files
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
    """
    file_timespan = rule.file_timespan
    if "time" not in da.dims:
        # climatology
        filepath = create_filepath(da, rule)
        da.to_netcdf(filepath, mode="w", format="NETCDF4")
        return
    groups = da.resample(time=f"{file_timespan}D")
    paths = []
    datasets = []
    for group_name, group_ds in groups:
        paths.append(create_filepath(group_ds, rule))
        datasets.append(group_ds)
    xr.save_mfdataset(datasets, paths)
    return


"""
Cell Methods?? These are ignored at the momemt in the time-averaging step
area: depth: time: mean
area: mean
area: mean (comment: over land and sea ice) time: point
area: mean time: maximum
area: mean time: maximum within days time: mean over days
area: mean time: mean within days time: mean over days
area: mean time: mean within hours time: maximum over hours
area: mean time: mean within years time: mean over years
area: mean time: minimum
area: mean time: minimum within days time: mean over days
area: mean time: point
area: mean time: sum
area: mean where crops time: maximum
area: mean where crops time: maximum within days time: mean over days
area: mean where crops time: minimum
area: mean where crops time: minimum within days time: mean over days
area: mean where grounded_ice_sheet
area: mean where ice_free_sea over sea time: mean
area: mean where ice_sheet
area: mean where land
area: mean where land over all_area_types time: mean
area: mean where land over all_area_types time: point
area: mean where land over all_area_types time: sum
area: mean where land time: mean
area: mean where land time: mean (with samples weighted by snow mass)
area: mean where land time: point
area: mean where sea
area: mean where sea depth: sum where sea (top 100m only) time: mean
area: mean where sea depth: sum where sea time: mean
area: mean where sea time: mean
area: mean where sea time: point
area: mean where sea_ice (comment: mask=siconc) time: point
area: mean where sector time: point
area: mean where snow over sea_ice area: time: mean where sea_ice
area: point
area: point time: point
area: sum
area: sum where ice_sheet time: mean
area: sum where sea time: mean
area: time: mean
area: time: mean (comment: over land and sea ice)
area: time: mean where cloud
area: time: mean where crops (comment: mask=cropFrac)
area: time: mean where floating_ice_shelf (comment: mask=sftflf)
area: time: mean where grounded_ice_sheet (comment: mask=sfgrlf)
area: time: mean where ice_sheet
area: time: mean where natural_grasses (comment: mask=grassFrac)
area: time: mean where pastures (comment: mask=pastureFrac)
area: time: mean where sea_ice (comment: mask=siconc)
area: time: mean where sea_ice (comment: mask=siconca)
area: time: mean where sea_ice (comment: mask=siitdconc)
area: time: mean where sea_ice_melt_pond (comment: mask=simpconc)
area: time: mean where sea_ice_ridges (comment: mask=sirdgconc)
area: time: mean where sector
area: time: mean where shrubs (comment: mask=shrubFrac)
area: time: mean where snow (comment: mask=snc)
area: time: mean where trees (comment: mask=treeFrac)
area: time: mean where unfrozen_soil
area: time: mean where vegetation (comment: mask=vegFrac)
longitude: mean time: mean
longitude: mean time: point
longitude: sum (comment: basin sum [along zig-zag grid path]) depth: sum time: mean
time: mean
time: mean grid_longitude: mean
time: point
"""
