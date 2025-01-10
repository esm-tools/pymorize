"""
This module contains the functions that are used to cache the results of the tasks.

Functions
---------
generate_cache_key(task, inputs):
    Generate a cache key for the task based on its name and inputs.

manual_checkpoint(data, rule):
    Manually insert a checkpoint in the flow and return a Completed state.

inspect_cache(cache_dir="~/.prefect/storage"):
    Inspect the cache directory and log the contents of each file, attempting to decode them as JSON or pickle.

inspect_result(result):
    Inspect a cached result file, decode its base64 content, unpickle it, and return the unpickled result.
"""

import base64
import json
import pickle
from pathlib import Path

from prefect.states import Completed

from .logging import logger


def generate_cache_key(task, inputs):
    """
    Generate a cache key for the task.

    Parameters
    ----------
    task : object
        The task object for which the cache key is being generated.
    inputs : dict
        The inputs to the task.

    Returns
    -------
    str
        The generated cache key.
    """
    task_name = task.name
    input_hash = hash(json.dumps(inputs, sort_keys=True))
    cache_key = f"{task_name}_{input_hash}"
    return cache_key


def manual_checkpoint(data, rule):
    """
    Manually insert a checkpoint in the flow.

    Parameters
    ----------
    data : any
        The data to be stored at the checkpoint.
    rule : object
        The rule associated with the checkpoint.

    Returns
    -------
    Completed
        A Completed state indicating the checkpoint has been reached.
    """
    logger.info("Manually inserting checkpoint")
    return Completed(message="Checkpoint reached", data=data)


def inspect_cache(cache_dir="~/.prefect/storage"):
    """
    Inspect the cache directory and log the contents of each file.

    Parameters
    ----------
    cache_dir : str, optional
        The directory where cache files are stored. Defaults to "~/.prefect/storage".

    Logs
    ----
    Information about each file in the cache directory, including its name and content type (JSON or pickle).
    """
    cache_path = Path(cache_dir).expanduser()

    for file in cache_path.glob("*"):
        logger.info(f"File: {file.name}")
        try:
            with open(file, "rb") as f:
                # First, try to load as JSON
                try:
                    data = json.load(f)
                    logger.info("  Content type: JSON")
                    logger.info(f"  Content: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    # If not JSON, try to load as pickle
                    f.seek(0)
                    try:
                        data = pickle.load(f)
                        logger.info("  Content type: Pickle")
                        logger.info(f"  Content: {data}")
                    except pickle.UnpicklingError as e:
                        logger.error("  Unable to decode file content")
                        raise e
        except Exception as e:
            logger.error(f"  Error reading file: {str(e)}")
            raise e
        logger.info("\n")


def inspect_result(result):
    """
    Inspect a cached result file, decode its base64 content, unpickle it, and return the unpickled result.

    Parameters
    ----------
    result : str
        The path to the cached result file.

    Returns
    -------
    any
        The unpickled result object.
    """
    with open(result, "r") as file:
        cached_data = json.load(file)
    # FIXME: handle pickling library...
    pickled_result_base64 = cached_data["result"]
    pickled_result = base64.b64decode(pickled_result_base64)
    unpickled_result = pickle.loads(pickled_result)
    return unpickled_result
