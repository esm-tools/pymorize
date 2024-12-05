# global_attributes.py

import json
import re
from pathlib import Path

from .controlled_vocabularies import ControlledVocabularies

# from loguru import logger

cv = ControlledVocabularies.load_from_git()

required_global_attributes = cv["required_global_attributes"]

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


defaults = {
    "institution_id": "AWI",
    "license_type": "CC BY-SA 4.0",
    "maintainer_url": None,
}


def set_global_attributes(ds, rule):
    gattrs = {}
    variant_label = rule.get("variant_label")
    update_variant_label(variant_label, gattrs)
    variable_id = rule.data_request_variable.variable_id
    gattrs["variable_id"] = variable_id
    gattrs["table_id"] = rule.data_request_variable.table.table_id
    _update_global_attributes_from_table_header(gattrs, rule)
    gattrs["source_id"] = source_id = rule.get("source_id")
    source_id_cv = cv["source_id"][source_id]
    _institution_id = source_id_cv.get("institution_id")
    if len(_institution_id) > 1:
        institution_ids = ", ".join(_institution_id)
        institution_id = rule.get("institution_id")
        if institution_id is None:
            raise ValueError(
                f"institution_id -- {institution_ids} -- has multiple value for source_id {source_id}."
            )
        else:
            assert institution_id in _institution_id
    else:
        institution_id = _institution_id[0]
    gattrs["institution_id"] = institution_id
    license_type = source_id_cv["license_info"]["id"]
    further_info_url = rule.get("further_info_url")
    _update_license(gattrs, cv, institution_id, license_type, further_info_url)
    gattrs["source"] = source = rule.get("source")  # model_component
    gattrs["grid"] = source_id_cv["model_component"][source]["description"]
    gattrs["nominal_resolution"] = source_id_cv["model_component"][source][
        "native_nominal_resolution"
    ]
    gattrs["source_type"] = rule.get("source_type")
    experiment_id = rule.get("experiment_id")
    activity_id = rule.get("activity_id", None)
    if activity_id is None:
        _experiment_id_cv = cv.get("experiment_id", {}).get(experiment_id, {})
        activity_id = _experiment_id_cv.get("activity_id", [])
        if activity_id and len(activity_id) > 1:
            activity_ids = ", ".join(activity_id)
            raise ValueError(
                f"activity_id -- {activity_ids} -- has multiple value for experiment_id {experiment_id}."
            )
        elif activity_id:
            activity_id = activity_id[0]
        else:
            raise ValueError(f"no activity_id found for experiment_id {experiment_id}")
    gattrs["activity_id"] = activity_id
    gattrs["experiment"] = _experiment_id_cv.get("experiment", "")
    gattrs["experiment_id"] = experiment_id
    # ignore parent_experiment_id for now, in the first iteration
    # parent_activity_id = _experiment_id_cv.get("parent_activity_id", "")
    gattrs["sub_experiment"] = rule.get("sub_experiment", "")
    gattrs["sub_experiment_id"] = _experiment_id_cv.get("sub_experiment_id")


def _update_global_attributes_from_table_header(gattrs, rule):
    """Updates global attributes from table header"""
    table = rule.data_request_variable.table
    header = table._data["Header"]
    gattrs["data_specs_version"] = header["data_specs_version"]
    gattrs["Conventions"] = header["Conventions"]
    gattrs["mip_era"] = header["mip_era"]
    gattrs["realm"] = header["realm"]
    gattrs["product"] = header["product"]


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


def _update_variant_label(label: str, gattrs: dict) -> dict:
    "Add variant_label to global attributes"
    variant_label_indices = _parse_variant_label(label)
    gattrs |= variant_label_indices
    gattrs["variant_label"] = label
    return gattrs


def _update_license(
    gattrs: dict,
    cv: dict,
    institution_id: str = None,
    license_type: str = None,
    further_info_url: str = None,
):
    """
    Updates the license attribute in the global attributes dictionary.

    Args:
        gattrs (dict): The global attributes dictionary to update.
        cv (dict): The controlled vocabulary dictionary.
        institution_id (str, optional): The institution ID. Defaults to None.
        license_type (str, optional): The license type. Defaults to None.
        further_info_url (str, optional): The maintainer URL. Defaults to None.

    Returns:
        None

    Raises:
        None
    """

    institution_id = institution_id or defaults.get("institution_id")
    license_type = license_type or defaults.get("license_type")
    further_info_url = further_info_url or defaults.get("further_info_url")
    logger.debug(f"{institution_id=}")
    logger.debug(f"{license_type=}")
    logger.debug(f"{further_info_url=}")
    lic = cv["license"]
    license_text = lic["license"]
    license_id = lic["license_options"][license_type]["license_id"]
    license_url = lic["license_options"][license_type]["license_url"]
    if further_info_url is None:
        logger.debug(
            "Removing placeholder for maintainer url from license text as it is not provided."
        )
        license_text = re.sub(r"\[.*?\]", "", license_text)
    institution = cv["institution_id"][institution_id]

    def make_placeholders(text):
        return re.sub(r"<.*?>", "{}", text)

    logger.debug(
        "Creating place-holders in license template found in CMIP6_license.json"
    )
    text = make_placeholders(license_text)
    if further_info_url is None:
        text = text.format(institution, license_id, license_url)
    else:
        text = text.format(institution, license_id, license_url, further_info_url)
    logger.debug(f"License: {text}")
    gattrs["license"] = text
