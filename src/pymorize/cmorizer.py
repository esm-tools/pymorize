from pathlib import Path

import questionary
from dask.distributed import Client
from rich.progress import track

from .data_request import (DataRequest, DataRequestTable, DataRequestVariable,
                           IgnoreTableFiles)
from .logging import logger
from .pipeline import Pipeline
from .rule import Rule
from .validate import PIPELINES_VALIDATOR, RULES_VALIDATOR


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
        self._post_init_create_data_request()
        self._post_init_populate_rules_with_tables()
        self._post_init_data_request_variables()

    def _post_init_read_bare_tables(self):
        """
        Loads all the tables from table directory as a mapping object.
        A shortened version of the filename (i.e., ``CMIP6_Omon.json`` -> ``Omon``) is used as the mapping key.
        The same key format is used in CMIP6_table_id.json
        """
        table_dir = Path(self._general_cfg["CMIP_Tables_Dir"])
        table_files = {
            path.stem.replace("CMIP6_", ""): path for path in table_dir.glob("*.json")
        }
        tables = {}
        ignore_files = set(ignore_file.value for ignore_file in IgnoreTableFiles)
        for tbl_name, tbl_file in table_files.items():
            logger.debug(f"{tbl_name}, {tbl_file}")
            if tbl_file.name not in ignore_files:
                logger.debug(f"Adding Table {tbl_name}")
                tables[tbl_name] = DataRequestTable(tbl_file)
        self._general_cfg["tables"] = self.tables = tables

    def _post_init_create_data_request(self):
        """
        Creates a DataRequest object from the tables directory.
        """
        table_dir = self._general_cfg["CMIP_Tables_Dir"]
        self.data_request = DataRequest.from_tables_dir(table_dir)

    def _post_init_populate_rules_with_tables(self):
        """
        Populates the rules with the tables in which the variable described by that rule is found.
        """
        tables = self._general_cfg["tables"]
        for rule in self.rules:
            for tbl in tables.values():
                if rule.cmor_variable in tbl.variable_ids:
                    rule.add_table(tbl)

    def _post_init_data_request_variables(self):
        for drv in self.data_request.variables:
            rule_for_var = self.find_matching_rule(drv)
            if rule_for_var is None:
                continue
            if rule_for_var.data_request_variables == []:
                rule_for_var.data_request_variables = [drv]
            else:
                rule_for_var.data_request_variables.append(drv)
        # FIXME: This needs a better name...
        self._rules_expand_drvs()
        self._rules_depluralize_drvs()

    def find_matching_rule(
        self, data_request_variable: DataRequestVariable
    ) -> Rule or None:
        matches = []
        attr_criteria = [("cmor_variable", "variable_id")]
        for rule in self.rules:
            if all(
                getattr(rule, r_attr) == getattr(data_request_variable, drv_attr)
                for (r_attr, drv_attr) in attr_criteria
            ):
                matches.append(rule)
        if len(matches) == 0:
            msg = f"No rule found for {data_request_variable}"
            if self._pymorize_cfg.get("raise_on_no_rule", False):
                raise ValueError(msg)
            else:
                logger.warning(msg)
            return None
        if len(matches) > 1:
            msg = f"Need only one rule to match to {data_request_variable}. Found {len(matches)}."
            if self._pymorize_cfg.get("raise_on_multiple_rules", True):
                raise ValueError(msg)
            else:
                logger.critical(msg)
                logger.critical(
                    "This should lead to a program crash! Exception due to >> pymorize_cfg['raise_on_multiple_rules'] = False <<"
                )
                logger.warning("Returning the first match.")
        return matches[0]

    # FIXME: This needs a better name...
    def _rules_expand_drvs(self):
        new_rules = []
        for rule in self.rules:
            if len(rule.data_request_variables) == 1:
                new_rules.append(rule)
            else:
                cloned_rules = rule.expand_drvs()
                for rule in cloned_rules:
                    new_rules.append(rule)
        self.rules = new_rules

    def _rules_depluralize_drvs(self):
        for rule in self.rules:
            assert len(rule.data_request_variables) == 1
            drv = rule.data_request_variable = rule.data_request_variables[0]
            drv.depluralize()

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
        if "rules" in data:
            if not RULES_VALIDATOR.validate({"rules": data["rules"]}):
                raise ValueError(RULES_VALIDATOR.errors)
        for rule in data.get("rules", []):
            rule_obj = Rule.from_dict(rule)
            instance.add_rule(rule_obj)
        if "pipelines" in data:
            if not PIPELINES_VALIDATOR.validate({"pipelines": data["pipelines"]}):
                raise ValueError(PIPELINES_VALIDATOR.errors)
        for pipeline in data.get("pipelines", []):
            pipeline_obj = Pipeline.from_dict(pipeline)
            instance.add_pipeline(pipeline_obj)

        instance._post_init_populate_rules_with_tables()
        instance._post_init_create_data_request()
        instance._post_init_data_request_variables()
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
                if self._pymorize_cfg.get("raise_on_no_rule", False):
                    raise ValueError(f"No rule found for {cmor_variable}")
                elif self._pymorize_cfg.get("warn_on_no_rule", True):
                    # FIXME(PG): This should be handled by the logger automatically
                    if not self._pymorize_cfg.get("quiet", True):
                        logger.warning(f"No rule found for {cmor_variable}")
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
            data = pipeline.run(data, rule)
        return data
