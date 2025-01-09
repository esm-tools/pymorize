"""
This module contains the functions to manage the Dask cluster.
"""

from contextlib import contextmanager

import dask
from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster

from .logging import logger

CLUSTER_MAPPINGS = {
    "local": LocalCluster,
    "slurm": SLURMCluster,
}
CLUSTER_SCALE_SUPPORT = {"local": False, "slurm": True}
CLUSTER_ADAPT_SUPPORT = {"local": False, "slurm": True}


def set_dashboard_link(cluster):
    """
    Checks whether the default user configuration for the dashboard link is valid.
    If the configuration is invalid it tried to catch the following errors:

    * ``KeyError``: 'JUPYTERHUB_SERVICE_PREFIX' -> The dashboard link is not valid because
      the cluster was not launched from JupyterHub. In this case, the default dashboard
      link is set to 'http://{host}:8787'.

    Parameters
    ----------
    cluster : dask_jobqueue.SLURMCluster
        The Dask cluster to set the dashboard link.
    """
    try:
        _ = cluster.dashboard_link
    except KeyError as e:
        if "JUPYTERHUB_SERVICE_PREFIX" in str(e):
            logger.debug(
                "Trying to use JupyterHub prefix for the dashboard link, but the it "
                "was not launched from JupyterHub. Falling back to the default "
                "dashboard link."
            )
            default_dashboard_link = "http://{host}:8787"
            dask.config.set({"distributed.dashboard.link": default_dashboard_link})
        else:
            raise e


class DaskContext:
    """
    Global singleton to store the current Dask cluster.
    """

    _current_cluster = None

    @classmethod
    @contextmanager
    def set_cluster(cls, cluster):
        logger.info(f"Setting Dask cluster {cluster=} in context!")
        cls._current_cluster = cluster
        try:
            yield
        finally:
            logger.info("Removing Dask cluster from context!")
            cls._current_cluster = None

    @classmethod
    def get_cluster(cls):
        if cls._current_cluster is None:
            raise RuntimeError("No active Dask cluster in context!")
        return cls._current_cluster
