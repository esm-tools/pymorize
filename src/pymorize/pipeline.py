"""
Pipeline of the data processing steps.
"""

import json
import os

import randomname
from prefect import flow
from prefect.tasks import Task
from prefect_dask import DaskTaskRunner

from .logging import logger
from .utils import get_callable_by_name


class Pipeline:
    def __init__(self, *args, name=None, workflow_backend="prefect", dask_cluster=None):
        self._steps = args
        self.name = name or randomname.get_name()
        self._workflow_backend = workflow_backend
        self._cluster = dask_cluster

        if self._workflow_backend == "prefect":
            self._prefectize_steps()

    def __str__(self):
        name_header = f"Pipeline: {self.name}"
        name_uline = "-" * len(name_header)
        step_header = "steps"
        step_uline = "-" * len(step_header)
        r_val = [name_header, name_uline, step_header, step_uline]
        for i, step in enumerate(self.steps):
            r_val.append(f"[{i+1}/{len(self.steps)}] {step.__name__}")
        return "\n".join(r_val)

    def assign_cluster(self, cluster):
        logger.debug("Assinging cluster to this pipeline")
        self._cluster = cluster

    def _prefectize_steps(self):
        # Turn all steps into Prefect tasks:
        prefect_tasks = []
        for i, step in enumerate(self._steps):
            logger.debug(
                f"[{i+1}/{len(self._steps)}] Converting step {step.__name__} to Prefect task."
            )
            prefect_tasks.append(Task(step))

        self._steps = prefect_tasks

    @property
    def steps(self):
        return self._steps

    def run(self, data, rule_spec):
        if self._workflow_backend == "native":
            return self._run_native(data, rule_spec)
        elif self._workflow_backend == "prefect":
            return self._run_prefect(data, rule_spec)
        else:
            raise ValueError("Invalid workflow backend!")

    def _run_native(self, data, rule_spec):
        for step in self.steps:
            data = step(data, rule_spec)
        return data

    def _run_prefect(self, data, rule_spec):
        logger.debug(
            f"Dynamically creating workflow with DaskTaskRunner using {self._cluster=}..."
        )
        cmor_name = rule_spec.get("cmor_name")
        rule_name = rule_spec.get("name", cmor_name)

        @flow(
            flow_run_name=f"{self.name} - {rule_name}",
            description=f"{rule.get('description', '')}",
            task_runner=DaskTaskRunner(address=self._cluster.scheduler_address),
        )
        def dynamic_flow(data, rule_spec):
            return self._run_native(data, rule_spec)

        return dynamic_flow(data, rule_spec)

    @classmethod
    def from_list(cls, steps, name=None):
        return cls(*steps, name=name)

    @classmethod
    def from_qualname_list(cls, qualnames: list, name=None):
        return cls.from_list(
            [get_callable_by_name(name) for name in qualnames], name=name
        )

    @classmethod
    def from_dict(cls, data):
        if "uses" in data and "steps" in data:
            raise ValueError("Cannot have both 'uses' and 'steps' to create a pipeline")
        if "uses" in data:
            # FIXME(PG): This is bad. What if I need to pass arguments to the constructor?
            return get_callable_by_name(data["uses"])(name=data.get("name"))
        if "steps" in data:
            return cls.from_qualname_list(data["steps"], name=data.get("name"))
        raise ValueError("Pipeline data must have 'uses' or 'steps' key")


class FrozenPipeline(Pipeline):
    """
    The FrozenPipeline class is a subclass of the Pipeline class. It is designed to have a fixed set of steps
    that cannot be modified, hence the term "frozen". The specific steps are defined as a class-level constant
    and cannot be customized, only the name of the pipeline can be customized.

    Parameters
    ----------
    *args
        Variable length argument list. Not used in this class, but included for compatibility with parent.
    name : str, optional
        The name of the pipeline. If not provided, it defaults to None.

    Attributes
    ----------
    STEPS : tuple
        A tuple containing the steps of the pipeline. This is a class-level attribute and cannot be modified.
    """

    @property
    def steps(self):
        return self._steps

    @steps.setter
    def steps(self, value):
        raise AttributeError("Cannot set steps on a FrozenPipeline")


class DefaultPipeline(FrozenPipeline):
    """
    The DefaultPipeline class is a subclass of the Pipeline class. It is designed to be a general-purpose pipeline
    for data processing. It includes steps for loading data and handling unit conversion. The specific steps are fixed
    and cannot be customized, only the name of the pipeline can be customized.

    Parameters
    ----------
    name : str, optional
        The name of the pipeline. If not provided, it defaults to "pymorize.pipeline.DefaultPipeline".
    """

    STEPS = (
        "pymorize.gather_inputs.load_mfdataset",
        "pymorize.generic.get_variable",
        "pymorize.timeaverage.compute_average",
        "pymorize.units.handle_unit_conversion",
        "pymorize.generic.trigger_compute",
        "pymorize.generic.show_data",
        "pymorize.files.save_dataset",
    )

    def __init__(self, name="pymorize.pipeline.DefaultPipeline"):
        steps = [get_callable_by_name(name) for name in self.STEPS]
        super().__init__(*steps, name=name)


class TestingPipeline(FrozenPipeline):
    """
    The TestingPipeline class is a subclass of the Pipeline class. It is designed for testing purposes. It includes
    steps for loading data fake data, performing a logic step, and saving data. The specific steps are fixed and
    cannot be customized, only the name of the pipeline can be customized.

    Parameters
    ----------
    name : str, optional
        The name of the pipeline. If not provided, it defaults to "pymorize.pipeline.TestingPipeline".

    Warning
    -------
    An internet connection is required to run this pipeline, as the load_data step fetches data from the internet.
    """

    __test__ = False  # Prevent pytest from thinking this is a test, as the class name starts with test.

    STEPS = (
        "pymorize.generic.dummy_load_data",
        "pymorize.generic.dummy_logic_step",
        "pymorize.generic.dummy_save_data",
    )

    def __init__(self, name="pymorize.pipeline.TestingPipeline"):
        steps = [get_callable_by_name(name) for name in self.STEPS]
        super().__init__(*steps, name=name)
