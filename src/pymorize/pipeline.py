"""
Pipeline of the data processing steps.
"""

import json
import os

import randomname
from loguru import logger

from .utils import get_callable_by_name


class PipelineDB:
    """
    This class provides a JSON-based database for managing pipeline data.
    It provides CRUD (Create, Read, Update, Delete) operations for pipeline data.
    The database is stored in a JSON file, with the filename based on the process ID and the ID of the pipeline object.
    """

    def __init__(self, pipeline, keep_db=False):
        """
        Initializes the PipelineDB object.

        Parameters
        ----------
        pipeline: object
            The pipeline object that this database is associated with.
        keep_db: bool, optional
            If True, the database file will not be deleted when the object is deleted. Default is False.
        """
        pid = os.getpid()
        self._db_file = f"pymorize_{pid}_pipeline_{id(pipeline)}.json"
        self._db = {}
        self._keep_db = keep_db

    def save(self):
        """
        Saves the in-memory database to a file.
        """
        with open(self._db_file, "w") as f:
            json.dump(self._db, f)

    def load(self):
        """
        Loads the database from a file into memory.
        If the file does not exist, initializes an empty database.
        """
        if os.path.exists(self._db_file):
            with open(self._db_file, "r") as f:
                self._db = json.load(f)
        else:
            self._db = {}

    def create(self, step, data):
        """
        Creates a new entry in the database.

        Parameters
        ----------
        step: function
            The step function.
        data: dict
            The data to be associated with the step.
        """
        self._db[f"{step.__name__}_{id(step)}"] = data

    def read(self, step, default={}):
        """
        Reads an entry from the database.

        Parameters
        ----------
        step: function
            The step function.

        Returns
        -------
        dict
            The data associated with the step.
        """
        return self._db.get(f"{step.__name__}_{id(step)}", default)

    def update(self, step, data):
        """
        Updates an entry in the database.

        Parameters
        ----------
        step : callable
            The step function.
        data : dict
            The data to be updated.

        Raises
        ------
        KeyError
            If the step is not found in the database.
        """
        step_dict = self._db[f"{step.__name__}_{id(step)}"]
        step_dict.update(data)

    def delete(self, step):
        """
        Deletes an entry from the database.

        Parameters
        ----------
        step: callable
            The step function.
        """
        del self._db[f"{step.__name__}_{id(step)}"]

    def __enter__(self):
        """
        Loads the database from a file into memory when entering the context.
        """
        self.load()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Saves the in-memory database to a file when exiting the context.
        """
        self.save()

    def __del__(self):
        """
        Removes the database file when the object is deleted if all steps have status "done".
        """
        if (
            all(step.get("status") == "done" for step in self._db.values())
            and os.path.exists(self._db_file)
            and not self._keep_db
        ):
            os.remove(self._db_file)

    def __contains__(self, step):
        return f"{step.__name__}_{id(step)}" in self._db


class Pipeline:
    def __init__(self, *args, name=None):
        self._steps = args
        self.name = name or randomname.get_name()
        self._db = PipelineDB(self)

    @property
    def steps(self):
        return self._steps

    def run(self, data, rule_spec, cmorizer):
        for step in self.steps:
            with self._db as db:
                if db.read(step).get("status") == "done":
                    continue
                else:
                    self._start_step(step)
                    data = step(data, rule_spec, cmorizer)
                    self._end_step(step)
        return data

    def _start_step(self, step):
        logger.debug(f"Starting step: {step.__name__}")
        with self._db as db:
            db.create(step, {"status": "running"})

    def _end_step(self, step):
        logger.debug(f"Ending step: {step.__name__}")
        with self._db as db:
            db.update(step, {"status": "done"})

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
            return cls.from_qualname_steps(data["steps"], name=data.get("name"))
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

    STEPS = ()

    def __init__(self, *args, name=None):
        super().__init__(*self.STEPS, name=name)

    @property
    def steps(self):
        return self.STEPS

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
        get_callable_by_name("pymorize.generic.load_data"),
        get_callable_by_name("pymorize.generic.create_cmor_directories"),
        get_callable_by_name("pymorize.units.handle_unit_conversion"),
    )

    def __init__(self, name="pymorize.pipeline.DefaultPipeline"):
        super().__init__(*self.STEPS, name=name)


class TestingPipeline(FrozenPipeline):
    """
    The TestingPipeline class is a subclass of the Pipeline class. It is designed for testing purposes. It includes
    steps for loading data fake data, performing a logic step, and saving data. The specific steps are fixed and cannot be
    customized, only the name of the pipeline can be customized.

    Parameters
    ----------
    name : str, optional
        The name of the pipeline. If not provided, it defaults to "pymorize.pipeline.TestingPipeline".

    Warning
    -------
    An internet connection is required to run this pipeline, as the load_data step fetches data from the internet.
    """

    STEPS = (
        get_callable_by_name("pymorize.test_helpers.load_data"),
        get_callable_by_name("pymorize.test_helpers.logic_step"),
        get_callable_by_name("pymorize.test_helpers.save_data"),
    )

    def __init__(self, name="pymorize.pipeline.TestingPipeline"):
        super().__init__(*self.STEPS, name=name)
