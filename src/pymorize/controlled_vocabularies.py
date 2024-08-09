import json
import os
import glob


class ControlledVocabularies(dict):
    @staticmethod
    def print_experiment_ids(cv_file):
        cv = ControlledVocabularies([cv_file])
        for k, v in cv["experiment_id"].items():
            print(
                f"{k} {v['start_year']}-{v['end_year']} parent:{', '.join(v['parent_experiment_id'])}"
            )

    @classmethod
    def new_from_dir(cls, cmip6_cvs_dir):
        json_files = glob.glob(os.path.join(cmip6_cvs_dir, "*.json"))
        return cls(json_files)

    def __init__(self, json_files):
        super().__init__()
        for f in json_files:
            d = self.dict_from_json_file(f)
            self.update(d)

    @staticmethod
    def dict_from_json_file(path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"file {path}: {e.msg}")
