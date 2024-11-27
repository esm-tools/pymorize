"""
This module contains the functions to manage the Dask cluster.
"""

import dask
from dask.distributed import LocalCluster
from dask_jobqueue import SLURMCluster

from .logging import logger

CLUSTER_MAPPINGS = {
        "local": LocalCluster,
        "slurm": SLURMCluster,
        }


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
