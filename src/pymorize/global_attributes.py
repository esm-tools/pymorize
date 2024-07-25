# global_attributes.pr

import re

_fields = (
    "activity_id",
    "Conventions",
    "creation_date",
    "date_specs_version",
    "experiment",
    "experiment_id",
    "forcing_index",
    "frequency",
    "further_info_url",
    "grid",
    "grid_label",
    "initialization_index",
    "institution",
    "institution_id",
    "license",
    "mip_era",
    "nominal_resolution",
    "physics_index",
    "product",
    "realization_index",
    "realm",
    "source",
    "source_id",
    "source_type",
    "sub_experiment",
    "sub_experiment_id",
    "table_id",
    "tracking_id",
    "variable_id",
    "variant_label",
)

_parent_fields = (
    "branch_method",
    "branch_time_in_child",
    "branch_time_in_parent",
    "parent_experiment_id",
    "parent_mip_era",
    "parent_source_id",
    "parent_time_units",
    "parent_variant_label",
)


def parse_variant_label(label: str) -> dict:
    "Extracts indices values from variant label."
    pattern = re.compile(
        r"r(?P<realization_index>\d+)"
        r"i(?P<initialization_index>\d+)"
        r"p(?P<physics_index>\d+)"
        r"f(?P<forcing_index>\d+)"
    )
    d = pattern.match(label)
    d = {name: int(val) for name, val in d.items()}
    return d


def update_variant_label(label: str, gattrs: dict) -> dict:
    "Add variant_label to global attributes"
    variant_label_indices = parse_variant_label(label)
    gattrs.update(variant_label_indices)
    gattrs["variant_label"] = label
    return gattrs
