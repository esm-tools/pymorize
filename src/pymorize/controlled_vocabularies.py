"""
Controlled Vocabularies for CMIP<x>
"""

from abc import abstractmethod
import json
import pathlib
import re
import uuid
import datetime
from .factory import MetaFactory


class ControlledVocabularies(metaclass=MetaFactory):
    def __init__(self, cv=None):
        self.cv = {}
        if cv is not None:
            self.update(cv)

    def update(self, cv):
        self.cv.update(cv)

    @classmethod
    @abstractmethod
    def from_path(cls, path):
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def from_dict(cls, mapping: dict):
        raise NotImplementedError()

    @abstractmethod
    def global_attributes(self, reference_dict):
        pass

    @abstractmethod
    def subdir_path(self, reference_dict):
        pass


class CMIP6ControlledVocabularies(ControlledVocabularies):

    @classmethod
    def from_dict(cls, mapping: dict):
        c = cls()
        c.update(mapping)
        return c

    @classmethod
    def from_path(cls, path):
        c = cls()
        CVs_dir = pathlib.Path(path) / "CMIP6_CVs"
        d = {}
        for _path in CVs_dir.glob("*.json"):
            d.update(json.loads(_path.read_text()))
        c.update(d)
        return c

    @property
    def required_global_attributes(self):
        return self.cv["required_global_attributes"]

    def global_attributes(self, rule_dict: dict) -> dict:
        d = {}
        for key in self.required_global_attributes:
            func = getattr(self, f"do_{key}")
            d[key] = func(rule_dict)
        return d

    def subdir_path(self, rule_dict: dict) -> str:
        mip_era = self.do_mip_era(rule_dict)
        activity_id = self.do_activity_id(rule_dict)
        institution_id = self.do_institution_id(rule_dict)
        source_id = self.do_source_id(rule_dict)
        experiment_id = self.do_experiment_id(rule_dict)
        member_id = self.do_variant_label(rule_dict)
        sub_experiment_id = self.do_sub_experiment_id(rule_dict)
        if sub_experiment_id != "none":
            member_id = f"{member_id}-{sub_experiment_id}"
        table_id = self.do_table_id(rule_dict)
        variable_id = self.do_variable_id(rule_dict)
        grid_label = self.do_grid_label(rule_dict)
        version = f"v{datetime.datetime.today().strftime('%Y%m%d')}"
        directory_path = f"{mip_era}/{activity_id}/{institution_id}/{source_id}/{experiment_id}/{member_id}/{table_id}/{variable_id}/{grid_label}/{version}"
        return directory_path

    def _variant_label_components(self, label: str):
        pattern = re.compile(
            r"r(?P<realization_index>\d+)"
            r"i(?P<initialization_index>\d+)"
            r"p(?P<physics_index>\d+)"
            r"f(?P<forcing_index>\d+)"
            r"$"
        )
        d = pattern.match(label)
        if d is None:
            raise ValueError(
                f"`label` must be of the form 'r<int>i<int>p<int>f<int>', Got: {label}"
            )
        d = {name: int(val) for name, val in d.groupdict().items()}
        return d

    def do_variant_label(self, rule_dict: dict):
        return rule_dict["variant_label"]

    def do_physics_index(self, rule_dict: dict):
        variant_label = self.do_variant_label(rule_dict)
        components = self._variant_label_components(variant_label)
        return components["physics_index"]

    def do_forcing_index(self, rule_dict: dict):
        variant_label = self.do_variant_label(rule_dict)
        components = self._variant_label_components(variant_label)
        return components["forcing_index"]

    def do_initialization_index(self, rule_dict: dict):
        variant_label = self.do_variant_label(rule_dict)
        components = self._variant_label_components(variant_label)
        return components["initialization_index"]

    def do_realization_index(self, rule_dict: dict):
        variant_label = self.do_variant_label(rule_dict)
        components = self._variant_label_components(variant_label)
        return components["realization_index"]

    def do_source_id(self, rule_dict: dict):
        return rule_dict["source_id"]

    def do_source(self, rule_dict: dict):
        # TODO: extend this to include all model components
        source_id = self.do_source_id(rule_dict)
        cv_source_id = self.cv["source_id"][source_id]
        release_year = cv_source_id["release_year"]
        return f"{source_id} ({release_year})"

    def do_institution_id(self, rule_dict: dict):
        source_id = self.do_source_id(rule_dict)
        cv_source_id = self.cv["source_id"][source_id]
        institution_ids = cv_source_id["institution_id"]
        if len(institution_ids) > 1:
            user_institution_id = rule_dict.get("institution_id", None)
            if user_institution_id:
                if user_institution_id not in institution_ids:
                    raise ValueError(
                        f"Institution ID '{user_institution_id}' is not valid. "
                        f"Allowed values: {institution_ids}"
                    )
                return user_institution_id
            raise ValueError(
                f"Multiple institutions are not supported, got: {institution_ids}"
            )
        return institution_ids[0]

    def do_institution(self, rule_dict: dict):
        institution_id = self.do_institution_id(rule_dict)
        return self.cv["institution_id"][institution_id]

    def do_realm(self, rule_dict: dict):
        return rule_dict["model_component"]

    def do_grid_label(self, rule_dict: dict):
        return rule_dict["grid_label"]

    def do_grid(self, rule_dict: dict):
        source_id = self.do_source_id(rule_dict)
        cv_source_id = self.cv["source_id"][source_id]
        model_component = self.do_realm(rule_dict)
        grid_description = cv_source_id["model_component"][model_component][
            "description"
        ]
        if grid_description == "none":
            # check if user has provided grid description
            user_grid_description = rule_dict.get(
                "description", rule_dict.get("grid", None)
            )
            if user_grid_description:
                grid_description = user_grid_description
        return grid_description

    def do_nominal_resolution(self, rule_dict: dict):
        source_id = self.do_source_id(rule_dict)
        cv_source_id = self.cv["source_id"][source_id]
        model_component = self.do_realm(rule_dict)
        cv_model_component = cv_source_id["model_component"][model_component]
        if "native_nominal_resolution" in cv_model_component:
            nominal_resolution = cv_model_component["native_nominal_resolution"]
        if "native_ominal_resolution" in cv_model_component:
            nominal_resolution = cv_model_component["native_ominal_resolution"]
        if nominal_resolution == "none":
            # check if user has provided nominal resolution
            user_nominal_resolution = rule_dict.get(
                "nominal_resolution", rule_dict.get("resolution", None)
            )
            if user_nominal_resolution:
                nominal_resolution = user_nominal_resolution
        return nominal_resolution

    def do_license(self, rule_dict: dict):
        institution_id = self.do_institution_id(rule_dict)
        source_id = self.do_source_id(rule_dict)
        cv_source_id = self.cv["source_id"][source_id]
        license_id = cv_source_id["license_info"]["id"]
        license_url = self.cv["license"]["license_options"][license_id]["license_url"]
        license_id = self.cv["license"]["license_options"][license_id]["license_id"]
        license_text = self.cv["license"]["license"]
        # make placeholders in license text
        license_text = re.sub(r"<.*?>", "{}", license_text)
        further_info_url = rule_dict.get("further_info_url", None)
        if further_info_url is None:
            license_text = re.sub(r"\[.*?\]", "", license_text)
            license_text = license_text.format(institution_id, license_id, license_url)
        else:
            license_text = license_text.format(
                institution_id, license_id, license_url, further_info_url
            )
        return license_text

    def do_experiment_id(self, rule_dict: dict):
        return rule_dict["experiment_id"]

    def do_experiment(self, rule_dict: dict):
        experiment_id = self.do_experiment_id(rule_dict)
        return self.cv["experiment_id"][experiment_id]["experiment"]

    def do_activity_id(self, rule_dict: dict):
        experiment_id = self.do_experiment_id(rule_dict)
        cv_experiment_id = self.cv["experiment_id"][experiment_id]
        activity_ids = cv_experiment_id["activity_id"]
        if len(activity_ids) > 1:
            user_activity_id = rule_dict.get("activity_id", None)
            if user_activity_id:
                if user_activity_id not in activity_ids:
                    raise ValueError(
                        f"Activity ID '{user_activity_id}' is not valid. "
                        f"Allowed values: {activity_ids}"
                    )
                return user_activity_id
            raise ValueError(
                f"Multiple activities are not supported, got: {activity_ids}"
            )
        return activity_ids[0]

    def do_sub_experiment_id(self, rule_dict: dict):
        experiment_id = self.do_experiment_id(rule_dict)
        cv_experiment_id = self.cv["experiment_id"][experiment_id]
        sub_experiment_ids = cv_experiment_id["sub_experiment_id"]
        sub_experiment_id = " ".join(sub_experiment_ids)
        return sub_experiment_id

    def do_sub_experiment(self, rule_dict: dict):
        sub_experiment_id = self.do_sub_experiment_id(rule_dict)
        if sub_experiment_id == "none":
            sub_experiment = "none"
        else:
            sub_experiment = sub_experiment_id.split()[0]
        return sub_experiment

    def do_source_type(self, rule_dict: dict):
        experiment_id = self.do_experiment_id(rule_dict)
        cv_experiment_id = self.cv["experiment_id"][experiment_id]
        source_type = " ".join(cv_experiment_id["required_model_components"])
        return source_type

    def do_table_id(self, rule_dict: dict):
        header = rule_dict["table_header"]
        return header.table_id

    def do_mip_era(self, rule_dict: dict):
        header = rule_dict["table_header"]
        return header.mip_era

    def do_frequency(self, rule_dict: dict):
        return rule_dict.get("frequency", None)

    def do_Conventions(self, rule_dict: dict):
        header = rule_dict["table_header"]
        return header.Conventions

    def do_product(self, rule_dict: dict):
        header = rule_dict["table_header"]
        return header.product

    def do_data_specs_version(self, rule_dict: dict):
        header = rule_dict["table_header"]
        return str(header.data_specs_version)

    def do_creation_date(self, rule_dict: dict):
        return rule_dict["creation_date"]

    def do_tracking_id(self, rule_dict: dict):
        return "hdl:21.14100/" + str(uuid.uuid4())

    def do_variable_id(self, rule_dict: dict):
        return rule_dict["cmor_variable"]

    def do_further_info_url(self, rule_dict: dict):
        mip_era = self.do_mip_era(rule_dict)
        institution_id = self.do_institution_id(rule_dict)
        source_id = self.do_source_id(rule_dict)
        experiment_id = self.do_experiment_id(rule_dict)
        sub_experiment_id = self.do_sub_experiment_id(rule_dict)
        variant_label = self.do_variant_label(rule_dict)
        return (
            f"https://furtherinfo.es-doc.org/"
            f"{mip_era}.{institution_id}.{source_id}.{experiment_id}.{sub_experiment_id}.{variant_label}"
        )


class CMIP7ControlledVocabularies(ControlledVocabularies):
    pass
