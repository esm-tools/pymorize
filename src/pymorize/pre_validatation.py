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


def is_subperiod(ds, rule):
    """
    Check if the frequency in the input file is a sub-period of the frequency specified in the table.

    Parameters
    ----------
    ds : xr.Dataset
        The input dataset.
    rule : Rule
        The rule object containing information about filepath.

    Returns
    -------
    bool
        True if the input frequency is a sub-period of the table frequency, False otherwise.
    """
    table_freq = _frequency_from_approx_interval(
        rule.data_request_variable.table.approx_interval
    )
    first_filenames = []
    for input_collection in rule.inputs:
        first_filenames.append(input_collection.files[0])
    if len(first_filenames) == 1:
        filename = first_filenames[0]
        data_freq = fc.get(filename).freq
    else:  # Multi-variable Rule, handle differently
        data_freqs = set([fc.get(filename).freq for filename in first_filenames])
        if len(data_freqs) != 1:
            raise ValueError(
                f"You have a compound variable and have multiple internal frequencies! This is not allowed: {data_freqs}"
            )
        data_freq = data_freqs[0]
    return pd.tseries.frequencies.is_subperiod(data_freq, table_freq)
