import json
import sys
from pathlib import Path

import questionary
import yaml
from loguru import logger

from .rule import Rule


class CMORizer:

    def __init__(
        self, cmor_table_dir, output_dir, pipelines=None, rules=None, **kwargs
    ):
        self._cmor_table_dir = cmor_table_dir
        self._output_dir = output_dir
        self._cmor_tables = {}
        for cmor_table in Path(cmor_table_dir).iterdir():
            with open(cmor_table) as f:
                self._cmor_tables[cmor_table.stem] = json.load(f)
        self._rules = rules or []
        self._pipelines = pipelines or []

    def _post_init_checks(self):
        # Sanity Checks:
        self._check_rules_for_table()
        self._check_rules_for_output_dir()

    @classmethod
    def from_dict(cls, data):
        instance = cls(data["cmor_table_dir"], data["output_dir"])
        for rule in data.get("rules", []):
            instance.add_rule(Rule.from_dict(rule))
        # for pipeline in data.get("pipelines", []):
        #    instance.add_pipeline(Pipeline.from_dict(pipeline))
        return instance

    def add_rule(self, rule):
        if not isinstance(rule, Rule):
            raise TypeError("rule must be an instance of Rule")
        self._rules.append(rule)

    def _rule_for_filepath(self, filepath):
        filepath = str(filepath)
        matching_rules = []
        for rule in self._rules:
            for pattern in rule.input_patterns:
                if pattern.match(filepath):
                    matching_rules.append(rule)
        return matching_rules

    def _rule_for_cmor_variable(self, cmor_variable):
        matching_rules = []
        for rule in self._rules:
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
        for rule in self._rules:
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

    def __call__(self, filepath):
        rule = self._rule_for_filepath(filepath)
        if rule is None:
            logger.warning(f"No rule found for {filepath}")
            continue_anyway = questionary.confirm("Continue anyway? ").ask()
            if continue_anyway:
                logger.info(f"Skipping {filepath} as no rule was found")
            else:
                logger.error(f"Aborting, as no rule was found for {filepath}")
                sys.exit(1)
        else:
            for action in rule.actions:
                action(filepath)
