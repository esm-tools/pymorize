"""
Controlled vocabularies for CMIP6
"""

import glob
import json
import os


class ControlledVocabularies(dict):
    """Controlled vocabularies for CMIP6"""

    def __init__(self, json_files):
        """Create a new ControlledVocabularies object from a list of json files

        Parameters
        ----------
        json_files : list
            List of json files to load

        Returns
        -------
        ControlledVocabularies
            A new ControlledVocabularies object, behaves like a dictionary.
        """
        super().__init__()
        for f in json_files:
            d = self.dict_from_json_file(f)
            self.update(d)

    @classmethod
    def new_from_dir(cls, cmip6_cvs_dir):
        """Create a new ControlledVocabularies object from a directory of json files

        Parameters
        ----------
        cmip6_cvs_dir : str
            Path to the directory containing the json files
        """
        json_files = glob.glob(os.path.join(cmip6_cvs_dir, "*.json"))
        return cls(json_files)

    def print_experiment_ids(self):
        """Print experiment ids with start and end years and parent experiment ids"""
        for k, v in self["experiment_id"].items():
            print(
                f"{k} {v['start_year']}-{v['end_year']} parent:{', '.join(v['parent_experiment_id'])}"
            )

    @staticmethod
    def dict_from_json_file(path):
        """Load a json file into a dictionary object

        Parameters
        ----------
        path : str
            Path to the json file to load

        Raises
        ------
        ValueError
            If the file cannot be loaded
        """
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"file {path}: {e.msg}")
