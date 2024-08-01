# global_attributes.py

import re


# TODO: no need to hard-code these values, can be directly read from cmip6-cmor-tables/Tables/CMIP6_CV.json
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
    """Extracts indices values from variant label.
    `label` must be of the form "r<int>i<int>p<int>f<int>".
    Example: "r1i1p1f1"
    """
    pattern = re.compile(
        r"r(?P<realization_index>\d+)"
        r"i(?P<initialization_index>\d+)"
        r"p(?P<physics_index>\d+)"
        r"f(?P<forcing_index>\d+)"
        r"$"
    )
    if label is None:
        raise ValueError(
            f"`label` must be of the form 'r<int>i<int>p<int>f<int>', Got: {label}"
        )
    d = pattern.match(label)
    if d is None:
        raise ValueError(
            f"`label` must be of the form 'r<int>i<int>p<int>f<int>', Got: {label}"
        )
    d = {name: int(val) for name, val in d.groupdict().items()}
    return d


def update_variant_label(label: str, gattrs: dict) -> dict:
    "Add variant_label to global attributes"
    variant_label_indices = parse_variant_label(label)
    gattrs |= variant_label_indices
    gattrs["variant_label"] = label
    return gattrs
