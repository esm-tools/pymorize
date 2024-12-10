# global_attributes.py

import json
import re
from pathlib import Path
from datetime import datetime

from .controlled_vocabularies import ControlledVocabularies

# from loguru import logger

data = ControlledVocabularies.load_from_git()

required_global_attributes = data["required_global_attributes"]

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


"""
attribute dependencies
----------------------
Table header
------------
data_specs_version
Conventions
mip_era
realm
product
frequency

CV
---
source_id
    source
    institution_id
    license_info
    model_component  # how to get model_component
        native_nominal_resolution (nominal_resolution)
        description (grid)
experiment_id
    activity_id
    parent_experiment_id
    sub_experiment_id

User input
----------
table_id
further_info_url
institution
variant_label
    initialization_index
    realization_index
    forcing_index
    physics_index

system generated
----------------
creation_date
tracking_id
"""


def _parse_variant_label(label: str) -> dict:
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


def _source_id_related(rule):
    source_id = rule.source_id
    cv = data["source_id"][source_id]
    _inst_id = getattr(rule, "institution_id", None)
    inst_id = cv["institution_id"]
    if _inst_id:
        assert _inst_id in inst_id
    else:
        if len(inst_id) > 1:
            raise ValueError(
                f"Provide institution_id. Mutiple values for institution_id found {inst_id}"
            )
        _inst_id = next(iter(inst_id))
    model_components = cv["model_component"]
    model_component = getattr(rule, "model_component", None)
    if model_component:
        assert model_component in model_components
    else:
        raise ValueError("Missing required attribute 'model_component'")
    grid = model_components[model_component]["description"]
    nominal_resolution = model_components[model_component]["native_nominal_resolution"]
    license_id = cv["license_info"]["id"]
    license_url = data["license"]["license_options"][license_id]["license_url"]
    license_id = data["license"]["license_options"][license_id]["license_id"]
    license_text = data["license"]["license"]
    # make placeholders in license text
    license_text = re.sub(r"<.*?>", "{}", license_text)
    further_info_url = getattr(rule, "further_info_url", None)
    if further_info_url is None:
        license_text = re.sub(r"\[.*?\]", "", license_text)
        license_text = license_text.format(_inst_id, license_id, license_url)
    else:
        license_text = license_text.format(
            _inst_id, license_id, license_url, further_info_url
        )
    grid_label = getattr(rule, "grid_label", None)
    if grid_label is None:
        raise ValueError("Missing required attribute `grid_label`")
    return {
        "source_id": source_id,
        "source": f"{model_component} ({cv['release_year']})",
        "institution_id": _inst_id,
        "institution": data["institution_id"][_inst_id],
        "grid": grid,
        "grid_label": grid_label,
        "nominal_resolution": nominal_resolution,
        "license": license_text,
    }


def _experiment_id_related(rule):
    exp_id = rule.experiment_id
    cv = data["experiment_id"][exp_id]
    _activity_id = getattr(rule, "activity_id", None)
    activity_id = cv["activity_id"]
    if _activity_id:
        assert _activity_id in activity_id
    else:
        if len(activity_id) > 1:
            raise ValueError(f"Mutiple activity_id found {activity_id}")
        _activity_id = next(iter(activity_id))
    return {
        "activity_id": _activity_id,
        "experiment_id": exp_id,
        "experiment": cv["experiment"],
        "sub_experiment_id": " ".join(cv["sub_experiment_id"]),
        "source_type": " ".join(cv["required_model_components"]),
    }


def _header_related(rule):
    d = {}
    d["table_id"] = rule.table.table_id
    d["mip_era"] = rule.table.mip_era
    d["realm"] = rule.table.modeling_realm
    d["frequency"] = rule.table.frequency
    d["Conventions"] = rule.table.Conventions
    d["product"] = rule.table.product
    d["data_specs_version"] = rule.table.data_specs_version
    return d


def _set_global_attributes(rule):
    d = {}
    d["variable_id"] = rule.cmor_variable
    d["variant_label"] = rule.variant_label
    d.update(_header_related(rule))
    d.update(_parse_variant_label(rule.variant_label))
    d.update(_source_id_related(rule))
    d.update(_experiment_id_related(rule))
    d = {k: d[k] for k in sorted(d)}
    return d


def set_global_attributes(ds, rule):
    d = _set_global_attributes(rule)
    # this needs to be discussed. For now setting it to today's datetime
    # file creation date or today
    d["creation_date"] = str(datetime.today())
    # how to get proper tracking_id is yet to be determined
    # This is just the tracking prefix
    d["tracking_id"] = "hdl:21.14100"
    ds.attrs.update(d)
    return ds
