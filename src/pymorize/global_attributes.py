import xarray as xr


def set_global_attributes(ds: xr.DataArray, rule):
    """
    Set global attributes on a dataset.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset to set the global attributes on.
    rule : DataRequestRule
        The rule to extract the global attributes from.
    """
    # Get the global attributes set on rule
    rule_attrs = rule.global_attributes_set_on_rule()
    global_attributes = rule.controlledvocabularies.global_attributes(rule_attrs)
    # Set the global attributes on the dataset
    ds.attrs.update(global_attributes)
    return ds
