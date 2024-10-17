# global_attributes.py

import re
import json
from pathlib import Path
# from loguru import logger

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


defaults = {
    "institution_id": "AWI",
    "license_type": "CC BY-SA 4.0",
    "maintainer_url": None,
}


def set_global_attributes(ds, rule):
    gattrs = {}
    cvs = rule.get("cvs", {})
    variant_label = rule.get("variant_label")
    update_variant_label(variant_label, gattrs)
    source_id = rule.get("source_id")
    experiment_id = rule.get("experiment_id")
    activity_id = rule.get("activity_id", None)
    if activity_id is None:
        _experiment_id_cv = cvs.get("experiment_id", {}).get(experiment_id, {})
        activity_id = _experiment_id_cv.get("activity_id", [])
        if activity_id and len(activity_id) > 1:
            activity_ids = ", ".join(activity_id)
            raise ValueError(
                f"activity_id -- {activity_ids} -- has multiple value for experiment_id {experiment_id}."
            )

    experiment = _experiment_id_cv.get("experiment", "")
    parent_activity_id = _experiment_id_cv.get("parent_activity_id", "")


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


def load_cvs(path: Path):
    "Loads all controlled vocabilaries at given path as dict mapping"
    d = {}
    for p in path.glob("*.json"):
        with open(p) as fid:
            d |= json.load(fid)
    d.pop("version_metadata")
    return d


def update_license(
    gattrs: dict,
    cv: dict,
    institution_id: str = None,
    license_type: str = None,
    maintainer_url: str = None,
):
    """
    Updates the license attribute in the global attributes dictionary.

    Args:
        gattrs (dict): The global attributes dictionary to update.
        cv (dict): The controlled vocabulary dictionary.
        institution_id (str, optional): The institution ID. Defaults to None.
        license_type (str, optional): The license type. Defaults to None.
        maintainer_url (str, optional): The maintainer URL. Defaults to None.

    Returns:
        None

    Raises:
        None
    """

    institution_id = institution_id or defaults.get("institution_id")
    license_type = license_type or defaults.get("license_type")
    maintainer_url = maintainer_url or defaults.get("maintainer_url")
    logger.debug(f"{institution_id=}")
    logger.debug(f"{license_type=}")
    logger.debug(f"{maintainer_url=}")
    lic = cv["license"]
    license_text = lic["license"]
    license_id = lic["license_options"][license_type]["license_id"]
    license_url = lic["license_options"][license_type]["license_url"]
    if maintainer_url is None:
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
    if maintainer_url is None:
        text = text.format(institution, license_id, license_url)
    else:
        text = text.format(institution, license_id, license_url, maintainer_url)
    logger.debug(f"License: {text}")
    gattrs["license"] = text
