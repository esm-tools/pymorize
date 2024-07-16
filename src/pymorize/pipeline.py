"""
Pipeline of the data processing steps.
"""

import json
import os

from loguru import logger

from .utils import get_callable_by_name


class PipelineDB:
    """
    This class provides a JSON-based database for managing pipeline data.
    It provides CRUD (Create, Read, Update, Delete) operations for pipeline data.
    The database is stored in a JSON file, with the filename based on the process ID and the ID of the pipeline object.

    Attributes:
    -----------
    _db_file : str
        The name of the file where the database is stored. Internal use only!
    _db : dict
        The in-memory representation of the database. Internal use only!

    Methods:
    --------
    save():
        Saves the in-memory database to a file.
    load():
        Loads the database from a file into memory.
    create(step, data):
        Creates a new entry in the database.
    read(step):
        Reads an entry from the database.
    update(step, data):
        Updates an entry in the database.
    delete(step):
        Deletes an entry from the database.
    """

    def __init__(self, pipeline, keep_db=False):
        """
        Initializes the PipelineDB object.

        Parameters:
        -----------
        pipeline: object
            The pipeline object that this database is associated with.
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

        Parameters:
        -----------
        step: function
            The step function.
        data: dict
            The data to be associated with the step.
        """
        self._db[f"{step.__name__}_{id(step)}"] = data

    def read(self, step, default={}):
        """
        Reads an entry from the database.

        Parameters:
        -----------
        step: function
            The step function.

        Returns:
        --------
        dict
            The data associated with the step.
        """
        return self._db.get(f"{step.__name__}_{id(step)}", default)

    def update(self, step, data):
        """
        Updates an entry in the database.

        Parameters:
        -----------
        step: function
            The step function.
        data: dict
            The data to be updated.

        Raises:
        -------
        KeyError: If the step is not found in the database.
        """
        step_dict = self._db[f"{step.__name__}_{id(step)}"]
        step_dict.update(data)

    def delete(self, step):
        """
        Deletes an entry from the database.

        Parameters:
        -----------
        step: function
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
    def __init__(self, *args):
        self.steps = args
        self._db = PipelineDB(self)

    def run(self, data):
        for step in self.steps:
            with self._db as db:
                if db.read(step).get("status") == "done":
                    continue
                else:
                    self._start_step(step)
                    data = step(data)
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
    def from_list(cls, steps):
        return cls(*steps)

    @classmethod
    def from_qualname_list(cls, qualnames: list):
        return cls.from_list(get_callable_by_name(name) for name in qualnames)


class DefaultPipeline(Pipeline):
    def __init__(self):
        super().__init__(
            # FIXME: Fill in with appropriate steps
            get_callable_by_name("pymorize.generic.load_data"),
        )
