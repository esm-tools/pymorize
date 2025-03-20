def add_pp_components(data, rule):
    """Adds together Net Primary Production components"""
    # This is a USER FUNCTION and therefore you need some human brainpower and knowledge
    # of your model in order to know what you want to do.

    data["pp"] = data["diags3d01"] + data["diags3d02"]
    # This return is mandatory for the pipeline to usefully continue
    # We return our new variable to be further processed:
    return data["pp"]  # Return type: DataArray!


def set_pp_units(data, rule):
    """Corrects missing units on PP"""
    # Again, a user function. Insider knowledge of REcoM is needed
    data["pp"].attrs["units"] = "molC m-2 day-1"
    # Actually, data is in mmol, so we do a "by hand" conversion here to get the mol correct
    data["pp"] *= 1e-6
    return data


def vertical_integration(data, rule):
    data = data.sum(dim="depth")
    return data


def manual_breakpoint(data, rule):
    breakpoint()
    return data
