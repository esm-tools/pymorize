"""
The cmorized data should place in a sub-directory according to the following construct
directory_path_template : "<mip_era>/<activity_id>/<institution_id>/<source_id>/<experiment_id>/<member_id>/<table_id>/<variable_id>/<grid_label>/<version>"

<version> has the form “vYYYYMMDD” (e.g., “v20160314”), indicating a representative date for the version. 


examples:

- "directory_path_example":
    "CMIP6/CMIP/MOHC/HadGEM3-GC31-MM/historical/r1i1p1f3/Amon/tas/gn/v20191207/"
- "directory_path_sub_experiment_example":
    "CMIP6/DCPP/MOHC/HadGEM3-GC31-MM/dcppA-hindcast/s1960-r1i1p1f2/Amon/tas/gn/v20200417/"
"""

import datetime
import pathlib
from .factory import create_factory
from .global_attributes import GlobalAttributes


def create_cmor_directories(rule):
    rule_attrs = rule.global_attributes_set_on_rule()

    # Compute the other global attributes using the controlled vocabularies
    global_attributes_factory = create_factory(GlobalAttributes)
    GlobalAttributesClass = global_attributes_factory.get("CMIP6")
    ga = GlobalAttributesClass(rule.controlled_vocabularies)
    global_attributes = ga.get_global_attributes(rule_attrs)

    mip_era = global_attributes["mip_era"]
    activity_id = global_attributes["activity_id"]
    institution_id = global_attributes["institution_id"]
    source_id = global_attributes["source_id"]
    experiment_id = global_attributes["experiment_id"]
    member_id = global_attributes["member_id"]
    sub_experiment_id = global_attributes["sub_experiment_id"]
    if sub_experiment_id != "none":
        member_id = f"{member_id}-{sub_experiment_id}"
    table_id = global_attributes["table_id"]
    variable_id = global_attributes["variable_id"]
    grid_label = global_attributes["grid_label"]
    version = f"v{datetime.datetime.today().strftime('%Y%m%d')}"
    directory_path = f"{mip_era}/{activity_id}/{institution_id}/{source_id}/{experiment_id}/{member_id}/{table_id}/{variable_id}/{grid_label}/{version}"
    output_directory = rule.output_directory
    cmor_directory = pathlib.Path(output_directory) / directory_path
    cmor_directory.mkdir(parents=True, exist_ok=True)
    # TODO:
    # need to replace the output directory set on the rule with the cmorized directory
    # is not allowed to overwrite attribute on rule object. need to figure out a way
    return directory_path
