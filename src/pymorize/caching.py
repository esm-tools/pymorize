"""
This module contains the functions that are used to cache the results of the tasks.
"""

import base64
import json
import pickle
from pathlib import Path

from prefect.states import Completed

from .logging import logger


def manual_checkpoint(data, rule):
    """Manually insert a checkpoint in the flow"""
    logger.info("Manually inserting checkpoint")
    return Completed(message="Checkpoint reached", return_value=data)


def inspect_cache(cache_dir="~/.prefect/storage"):
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
    with open(result, "r") as file:
        cached_data = json.load(file)
    # FIXME: handle pickling library...
    pickled_result_base64 = cached_data["result"]
    pickled_result = base64.b64decode(pickled_result_base64)
    unpickled_result = pickle.loads(pickled_result)
    return unpickled_result
