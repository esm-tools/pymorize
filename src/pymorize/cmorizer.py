from pathlib import Path

import dask
import questionary
import yaml
from dask.distributed import Client
from dask_jobqueue import SLURMCluster
from prefect import flow, task
from prefect.futures import wait
from prefect.logging import get_run_logger
from prefect_dask import DaskTaskRunner
from rich.progress import track

from .data_request import (DataRequest, DataRequestTable, DataRequestVariable,
                           IgnoreTableFiles)
from .logging import logger
from .pipeline import Pipeline
from .rule import Rule
from .utils import wait_for_workers
from .validate import PIPELINES_VALIDATOR, RULES_VALIDATOR


class CMORizer:
    def __init__(
        self,
        pymorize_cfg=None,
        general_cfg=None,
        pipelines_cfg=None,
        rules_cfg=None,
        dask_cfg=None,
        inherit_cfg=None,
        **kwargs,
    ):
        self._general_cfg = general_cfg or {}
        self._pymorize_cfg = pymorize_cfg or {}
        self._dask_cfg = dask_cfg or {}
        self._inherit_cfg = inherit_cfg or {}
        self.rules = rules_cfg or []
        self.pipelines = pipelines_cfg or []

        self._post_init_configure_dask()
        self._post_init_create_dask_cluster()
        self._post_init_create_pipelines()
        self._post_init_create_rules()
        self._post_init_read_bare_tables()
        self._post_init_create_data_request()
        self._post_init_populate_rules_with_tables()
        self._post_init_data_request_variables()

    def _post_init_configure_dask(self):
        """
        Sets up configuration for Dask-Distributed

        See Also
        --------
        https://docs.dask.org/en/stable/configuration.html?highlight=config#directly-within-python
        """
        import dask.distributed  # Needed to pre-populate config, noqa: F401
        import dask_jobqueue  # Needed to pre-populate config, noqa: F401

        logger.info("Updating Dask configuration. Changed values will be:")
        logger.info(yaml.dump(self._dask_cfg))
        dask.config.update(dask.config.config, self._dask_cfg)
        logger.info("Dask configuration updated!")

    def _post_init_create_dask_cluster(self):
        # FIXME: In the future, we can support PBS, too.
        logger.info("Setting up SLURMCluster...")
        self._cluster = SLURMCluster()
        cluster_mode = self._pymorize_cfg.get("cluster_mode", "adapt")
        if cluster_mode == "adapt":
            min_jobs = self._pymorize_cfg.get("minimum_jobs", 1)
            max_jobs = self._pymorize_cfg.get("maximum_jobs", 10)
            self._cluster.adapt(minimum_jobs=min_jobs, maximum_jobs=max_jobs)
        elif cluster_mode == "fixed":
            jobs = self._pymorize_cfg.get("fixed_jobs", 5)
            self._cluster.scale(jobs=jobs)
        else:
            raise ValueError(
                "You need to specify adapt or fixed for pymorize.cluster_mode"
            )
        # Wait for at least min_jobs to be available...
        # FIXME: Client needs to be available here?
        logger.info(f"SLURMCluster can be found at: {self._cluster=}")
        logger.info(f"Dashboard {self._cluster.dashboard_link}")

        dask_extras = 0
        logger.info("Importing Dask Extras...")
        if self._pymorize_cfg.get("use_flox", True):
            dask_extras += 1
            logger.info("...flox...")
            import flox  # noqa: F401
            import flox.xarray  # noqa: F401
        logger.info(f"...done! Imported {dask_extras} libraries.")

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
            elif self._pymorize_cfg.get("warn_on_no_rule", True):
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
                pl = Pipeline.from_dict(p)
                pl.assign_cluster(self._cluster)
                pipelines.append(Pipeline.from_dict(p))
            else:
                raise ValueError(f"Invalid pipeline configuration for {p}")
        self.pipelines = pipelines

    def _post_init_create_rules(self):
        self.rules = [Rule.from_dict(p) for p in self.rules if not isinstance(p, Rule)]
        self._post_init_inherit_rules()

    def _post_init_inherit_rules(self):
        for rule_attr, rule_value in self._inherit_cfg.items():
            for rule in self.rules:
                rule.set(rule_attr, rule_value)

    def _post_init_checks(self):
        # Sanity Checks:
        self._check_rules_for_table()
        self._check_rules_for_output_dir()

    @classmethod
    def from_dict(cls, data):
        instance = cls(
            pymorize_cfg=data.get("pymorize", {}),
            general_cfg=data.get("general", {}),
            dask_cfg={
                "distributed": data.get("distributed", {}),
                "jobqueue": data.get("jobqueue", {}),
            },
        )
        if "rules" in data:
            if not RULES_VALIDATOR.validate({"rules": data["rules"]}):
                raise ValueError(RULES_VALIDATOR.errors)
        for rule in data.get("rules", []):
            rule_obj = Rule.from_dict(rule)
            instance.add_rule(rule_obj)
        instance._post_init_inherit_rules()
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
        # Assign the cluster to this pipeline:
        pipeline.assign_cluster(self._cluster)
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
            parallel = self._pymorize_cfg.get("parallel", True)
        if parallel:
            return self.parallel_process()
        else:
            return self.serial_process()

    def parallel_process(self, backend="prefect"):
        if backend == "prefect":
            return self._parallel_process_prefect()
        elif backend == "dask":
            return self._parallel_process_dask()
        else:
            raise ValueError("Unknown backend for parallel processing")

    def _parallel_process_prefect(self):
        # prefect_logger = get_run_logger()
        # logger = prefect_logger
        # @flow(task_runner=DaskTaskRunner(address=self._cluster.scheduler_address))
        @flow
        def dynamic_flow():
            rule_results = []
            for rule in self.rules:
                rule_results.append(self._process_rule_prefect.submit(rule))
            wait(rule_results)
            return rule_results

        return dynamic_flow()

    def _parallel_process_dask(self, external_client=None):
        if external_client:
            client = external_client
        else:
            client = Client(cluster=self._cluster)  # start a local Dask client
        if wait_for_workers(client, 1):
            futures = [client.submit(self._process_rule, rule) for rule in self.rules]

            results = client.gather(futures)

            logger.success("Processing completed.")
            return results
        else:
            logger.error("Timeout reached waiting for dask cluster, sorry...")

    def serial_process(self):
        data = {}
        for rule in track(self.rules, description="Processing rules"):
            data[rule] = self._process_rule(rule)
        logger.success("Processing completed.")
        return data

    def _process_rule(self, rule):
        logger.info(f"Starting to process rule {rule}")
        # Match up the pipelines:
        rule.match_pipelines(self.pipelines)
        data = None
        if not len(rule.pipelines) > 0:
            logger.error("No pipeline defined, something is wrong!")
        for pipeline in rule.pipelines:
            logger.info(f"Running {str(pipeline)}")
            data = pipeline.run(data, rule)
        return data

    @task
    def _process_rule_prefect(self, rule):
        return self._process_rule(rule)
