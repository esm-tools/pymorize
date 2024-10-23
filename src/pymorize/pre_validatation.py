"""
Validation of the inputs in the yaml file.
This needs to be done before triggering the pipeline.

Things to validate:
  - downsampling: the frequency in source files must be >= the frequceny in tables
    - example: hourly data to daily or monthly or yearly
  - upsampling: <not supported>
    - exmaple: monthly data to hourly or daily

"""

import pandas as pd
from .timeaverage import _frequency_from_approx_interval
from .filecache import fc


def check_frequency(ds, rule):
    """
    Check if the frequency in the input file is a sub-period of the frequency specified in the table.

    Parameters
    ----------
    ds : xr.Dataset
        The input dataset.
    rule : Rule
        The rule object containing information for generating the filepath.

    Returns
    -------
    bool
        True if the input frequency is a sub-period of the table frequency, False otherwise.
    """
    table_freq = _frequency_from_approx_interval(
        rule.data_request_variable.table.approx_interval
    )
    # get this from filecache instead
    filename = rule.input_files[0]
    data_freq = fc.get(filename).freq
    # data_freq = pd.tseries.frequencies.infer_freq(ds.time.data)
    # if data_freq is None:
    #     nfreq = list(ds.time.data.diff().dropna().unique())
    #     if not len(nfreq) == 1:
    #         raise ValueError(f"Multiple freq. detected {nfreq}")
    #     data_freq = nfreq[0]
    return pd.tseries.frequencies.is_subperiod(data_freq, table_freq)


# determine the chunk size based on downsampling frequency.
# By default, each file is considered as a chunk but with
# this function, it should be possible to determine how many
# files should be considered as a chunk. The idea is to make
# sure that all files in a chunk are allocated on the same node.
#
# This function does not belong here.
#
# def get_chunksize(ds, rule):
#     # timespan: number of time steps in output file.
#     timespan = rule.timespan
#     # get this from filecache instead
#     data_freq = pd.tseries.frequencies.infer_freq(ds.time.data)
