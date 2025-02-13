"""
Global Attributes

Controlled Vocabularies for CMIP6 define a set of required global attributes that must
be set on a CMIP6 dataset. Setting some of the global attributes is relies on user input
and setting others is done automatically by consulting the controlled vocabularies. Also,
some of the global attributes are retrieved from the CMIP6 Table Header for a given variable.

The required user input for global attributes are set on rule via the yaml configuration
file.

Use the `get_global_attributes` method on `DataRequestVariable` to get the global attributes.
"""

import re
import uuid

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


class GlobalAttributes:
    def __init__(self, cv):
        """
        Parameters
        ----------
        cv : ControlledVocabularies
            Controlled Vocabularies for CMIP6.
        """
        self.cv = cv

    def _parse_variant_label(self, label: str) -> dict:
        """
        Extracts indices values from variant label.
        `label` must be of the form "r<int>i<int>p<int>f<int>".
        Example
        -------
        >>> label = "r1i1p1f1"
        >>> _parse_variant_label(label)
        {'realization_index': 1, 'initialization_index': 1, 'physics_index': 1, 'forcing_index': 1,}
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

    def _source_id_related(self, attrs_map_on_rule: dict) -> dict:
        source_id = attrs_map_on_rule.get("source_id")
        cv = self.cv["source_id"][source_id]
        cv_institution_ids = cv["institution_id"]
        user_institution_id = attrs_map_on_rule.get("institution_id", None)
        if user_institution_id:
            if user_institution_id not in cv_institution_ids:
                raise ValueError(
                    f"Institution ID '{user_institution_id}' is not valid. "
                    f"Allowed values: {cv_institution_ids}"
                )
            selected_institution_id = user_institution_id
        else:
            # No user-provided institution_id; infer it
            if len(cv_institution_ids) > 1:
                raise ValueError(
                    f"Multiple institution IDs found: {cv_institution_ids}. "
                    "Please specify one in the rule."
                )
            selected_institution_id = cv_institution_ids[0]
        model_components = cv["model_component"]
        user_model_component = attrs_map_on_rule.get("model_component", None)
        if user_model_component:
            if user_model_component not in model_components:
                raise ValueError(
                    f"Model component '{user_model_component}' is not valid. "
                    f"Allowed values: {model_components}"
                )
            model_component = user_model_component
        else:
            if len(model_components) > 1:
                raise ValueError(
                    f"Multiple model components found: {model_components}. "
                    "Please specify one in the rule."
                )
            model_component = model_components[0]
        native_nominal_resolution = model_components[model_component].get(
            "native_nominal_resolution", None
        )
        # either native_nominal_resolution does not exists or it may be set to "none"
        # in any case, user is expected to provide this information
        if native_nominal_resolution in (None, "none"):
            user_native_nominal_resolution = attrs_map_on_rule.get(
                "native_nominal_resolution", None
            )
            if user_native_nominal_resolution:
                native_nominal_resolution = user_native_nominal_resolution
            else:
                raise ValueError(
                    "Missing required attribute `native_nominal_resolution`"
                )
        grid_description = model_components[model_component].get("description", None)
        if grid_description in (None, "none"):
            user_grid_description = attrs_map_on_rule.get("description", None)
            if user_grid_description:
                grid_description = user_grid_description
            else:
                raise ValueError(
                    "Missing required attribute `description` (i.e. grid description)"
                )
        license_id = cv["license_info"]["id"]
        license_url = self.cv["license"]["license_options"][license_id]["license_url"]
        license_id = self.cv["license"]["license_options"][license_id]["license_id"]
        license_text = self.cv["license"]["license"]
        # make placeholders in license text
        license_text = re.sub(r"<.*?>", "{}", license_text)
        further_info_url = attrs_map_on_rule.get("further_info_url", None)
        if further_info_url is None:
            license_text = re.sub(r"\[.*?\]", "", license_text)
            license_text = license_text.format(
                selected_institution_id, license_id, license_url
            )
        else:
            license_text = license_text.format(
                selected_institution_id, license_id, license_url, further_info_url
            )
        grid_label = attrs_map_on_rule.get("grid_label", None)
        if grid_label is None:
            raise ValueError("Missing required attribute `grid_label`")
        return {
            "source_id": source_id,
            "source": f"{model_component} ({cv['release_year']})",
            "institution_id": selected_institution_id,
            "institution": self.cv["institution_id"][selected_institution_id],
            "grid": grid_description,
            "grid_label": grid_label,
            "nominal_resolution": native_nominal_resolution,
            "license": license_text,
        }

    def _experiment_id_related(self, attrs_map_on_rule: dict) -> dict:
        exp_id = attrs_map_on_rule.get("experiment_id")
        cv = self.cv["experiment_id"][exp_id]
        _activity_id = attrs_map_on_rule.get("activity_id", None)
        activity_id = cv["activity_id"]
        if _activity_id:
            assert _activity_id in activity_id
        else:
            if len(activity_id) > 1:
                raise ValueError(f"Mutiple activity_id found {activity_id}")
            _activity_id = next(iter(activity_id))
        sub_experiment_id = " ".join(cv["sub_experiment_id"])
        if sub_experiment_id == "none":
            sub_experiment = "none"
        else:
            sub_experiment = sub_experiment_id.split()[0]
        return {
            "activity_id": _activity_id,
            "experiment_id": exp_id,
            "experiment": cv["experiment"],
            "sub_experiment": sub_experiment,
            "sub_experiment_id": sub_experiment_id,
            "source_type": " ".join(cv["required_model_components"]),
        }

    def _header_related(self, attrs_map_on_rule: dict) -> dict:
        """
        Extracts header related global attributes from a DataRequestRule.

        Parameters
        ----------
        rule : DataRequestRule
            The data request rule to extract the header related global
            attributes from.

        Returns
        -------
        dict
            A dictionary of global attributes
        """
        d = {}
        header = attrs_map_on_rule["table_header"]
        d["table_id"] = header.table_id
        d["mip_era"] = header.mip_era
        d["realm"] = " ".join(header.realm) if isinstance(header.realm, list) else header.realm
        d["frequency"] = attrs_map_on_rule.get("frequency")
        d["Conventions"] = header.Conventions
        d["product"] = header.product
        d["data_specs_version"] = str(header.data_specs_version)
        return d

    def _creation_date(self, attrs_map_on_rule) -> dict:
        """Extracts the creation date of the parent directory of inputs in the rule."""
        return {"creation_date": attrs_map_on_rule.get("creation_date")}

    def _tracking_id(self, attrs_map_on_rule=None) -> dict:
        """Generates unique identifier for the dataset.

        As described in CMIP6_global_attributes_filenames_CVs document,
        `tracking_id` must be of the form “hdl:21.14100/<uuid>”. The
        document also recommends using the OSSP utility which supports
        a number of different DCE 1.1 variant UUID options.
        However, python uuid.uuid4 produces a compatible UUID and so
        it is used instead.

        Document reference: https://tinyurl.com/npjwpxrp
        seamore tool reference: https://tinyurl.com/2rnemxmb
        """
        return {"tracking_id": "hdl:21.14100/" + str(uuid.uuid4())}

    def get_global_attributes(self, attrs_map_on_rule: dict) -> dict:
        """
        Extracts all global attributes from a DataRequestRule.

        Parameters
        ----------
        attrs_map_on_rule : attributes set on DataRequestRule object
            The data request rule to extract the global attributes from.

        Returns
        -------
        dict
            A dictionary of global attributes.
        """
        d = {}
        d["variable_id"] = attrs_map_on_rule.get("cmor_variable")
        d["variant_label"] = attrs_map_on_rule.get("variant_label")
        d.update(self._header_related(attrs_map_on_rule))
        d.update(self._parse_variant_label(attrs_map_on_rule.get("variant_label")))
        d.update(self._source_id_related(attrs_map_on_rule))
        d.update(self._experiment_id_related(attrs_map_on_rule))
        d.update(self._creation_date(attrs_map_on_rule))
        d.update(self._tracking_id(attrs_map_on_rule))
        d = {k: d[k] for k in sorted(d)}
        return d

    def set_global_attributes(self, ds, attrs_map_on_rule: dict):
        """
        Set global attributes on a dataset based on the given rule.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset to set the global attributes on.
        rule : DataRequestRule
            The data request rule to use to set the attributes.

        Returns
        -------
        ds : xr.Dataset
            The dataset with the global attributes set.
        """
        d = self.get_global_attributes(attrs_map_on_rule)
        ds.attrs.update(d)
        return ds
