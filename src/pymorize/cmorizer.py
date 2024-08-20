from pathlib import Path
import json

import questionary
from dask.distributed import Client
from rich.progress import track

# from . import logging_helper
from .logging import logger
from .pipeline import Pipeline
from .rule import Rule
from .data_request import DataRequestTable


class CMORizer:

    def __init__(
        self,
        pymorize_cfg=None,
        general_cfg=None,
        pipelines_cfg=None,
        rules_cfg=None,
        **kwargs,
    ):
        self._general_cfg = general_cfg or {}
        self._pymorize_cfg = pymorize_cfg or {}
        self.rules = rules_cfg or []
        self.pipelines = pipelines_cfg or []

        self._post_init_create_pipelines()
        self._post_init_create_rules()
        self._post_init_read_bare_tables()
        self._post_init_populate_rules_with_tables()

    def _post_init_read_bare_tables(self):
        """
        Loads all the tables from table directory as a mapping object.
        A shortned version of the filename (i.e., CMIP6_Omon.json -> Omon) is used as the mapping key.
        The same key format is used in CMIP6_table_id.json
        """
        table_dir = self._general_cfg["CMIP_Tables_Dir"]
        table_files = {
            path.stem.replace("CMIP6_", ""): path
            for path in Path(table_dir).glob("*.json")
        }
        ignore = {"CV", "coordinate", "formula_terms", "grids", "input_example"}
        tables = {}
        for tbl_name, tbl_file in table_files.items():
            logger.debug(f"{tbl_name}, {tbl_file}")
            if tbl_name not in ignore:
                logger.debug(f"Adding Table {tbl_name}")
                tables[tbl_name] = DataRequestTable(tbl_file)
        self._general_cfg["tables"] = self.tables = tables

    def _post_init_populate_rules_with_tables(self):
        tables = self._general_cfg["tables"]
        # logger.debug(f"Inside {__name__}. Rules: {self.rules}")
        for rule in self.rules:
            logger.debug(f"Rule {rule}")
            var_name = rule.cmor_variable
            for tbl in tables.values():
                logger.debug(f"looking into table {tbl.table_id}")
                if var_name in tbl.variable_ids:
                    logger.debug(f"{var_name} is defined in Table {tbl.table_id}")
                    rule.add_table(tbl)

    def _post_init_data_request_variables(self):
        for rule in self.rules:
            rule.cmor_variable

    def _post_init_create_pipelines(self):
        pipelines = []
        for p in self.pipelines:
            if isinstance(p, Pipeline):
                pipelines.append(p)
            elif isinstance(p, dict):
                pipelines.append(Pipeline.from_dict(p))
            else:
                raise ValueError(f"Invalid pipeline configuration for {p}")
        self.pipelines = pipelines

    def _post_init_create_rules(self):
        self.rules = [Rule.from_dict(p) for p in self.rules if not isinstance(p, Rule)]

    def _post_init_checks(self):
        # Sanity Checks:
        self._check_rules_for_table()
        self._check_rules_for_output_dir()

    @classmethod
    def from_dict(cls, data):
        instance = cls(
            pymorize_cfg=data.get("pymorize", {}),
            general_cfg=data.get("general", {}),
        )
        for rule in data.get("rules", []):
            rule_obj = Rule.from_dict(rule)
            instance.add_rule(rule_obj)
        instance._post_init_populate_rules_with_tables()
        for pipeline in data.get("pipelines", []):
            pipeline_obj = Pipeline.from_dict(pipeline)
            instance.add_pipeline(pipeline_obj)
        return instance

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            raise TypeError("rule must be an instance of Rule")
        self.rules.append(rule)

    def add_pipeline(self, pipeline):
        if not isinstance(pipeline, Pipeline):
            raise TypeError("pipeline must be an instance of Pipeline")
        self.pipelines.append(pipeline)

    def _rule_for_filepath(self, filepath):
        filepath = str(filepath)
        matching_rules = []
        for rule in self.rules:
            for pattern in rule.input_patterns:
                if pattern.match(filepath):
                    matching_rules.append(rule)
        return matching_rules

    def _rule_for_cmor_variable(self, cmor_variable):
        matching_rules = []
        for rule in self.rules:
            if rule.cmor_variable == cmor_variable:
                matching_rules.append(rule)
        logger.debug(f"Found {len(matching_rules)} rules to apply for {cmor_variable}")
        return matching_rules

    def check_rules_for_table(self, table_name):
        missing_variables = []
        for cmor_variable in self._cmor_tables[table_name]["variable_entry"]:
            if self._rule_for_cmor_variable(cmor_variable) == []:
                logger.warning(f"No rule found for {cmor_variable}")
                missing_variables.append(cmor_variable)
        if missing_variables:
            logger.warning("This CMORizer may be incomplete or badly configured!")
            logger.warning(
                f"Missing rules for >> {len(missing_variables)} << variables."
            )

    def check_rules_for_output_dir(self, output_dir):
        all_files_in_output_dir = [f for f in Path(output_dir).iterdir()]
        for rule in self.rules:
            # Remove files from list when matching a rule
            for filepath in all_files_in_output_dir:
                if self._rule_for_filepath(filepath):
                    all_files_in_output_dir.remove(filepath)
        if all_files_in_output_dir:
            logger.warning("This CMORizer may be incomplete or badly configured!")
            logger.warning(
                f"Found >> {len(all_files_in_output_dir)} << files in output dir not matching any rule."
            )
            if questionary.confirm("Do you want to view these files?").ask():
                for filepath in all_files_in_output_dir:
                    logger.warning(filepath)

    def process(self, parallel=None):
        if parallel is None:
            parallel = self._pymorize_cfg.get("parallel", False)
        if parallel:
            return self.parallel_process()
        else:
            return self.serial_process()

    def parallel_process(self, external_client=None):
        if external_client:
            client = external_client
        else:
            client = Client()  # start a local Dask client

        futures = [client.submit(self._process_rule, rule) for rule in self.rules]

        results = client.gather(futures)

        logger.success("Processing completed.")
        return results

    def serial_process(self):
        data = {}
        for rule in track(self.rules, description="Processing rules"):
            data[rule] = self._process_rule(rule)
        logger.success("Processing completed.")
        return data

    def _process_rule(self, rule):
        # Match up the pipelines:
        rule.match_pipelines(self.pipelines)
        data = None
        for pipeline in rule.pipelines:
            data = pipeline.run(data, rule, self)
        return data
