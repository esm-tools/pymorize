"""
This module contains the functions that are used to cache the results of the tasks.
"""

from prefect.states import Completed

from .logging import logger


def manual_checkpoint(data, rule):
    """Manually insert a checkpoint in the flow"""
    logger.info(f"Manually inserting checkpoint")
    return Completed(message="Checkoint reached", return_value=data)
