"""
This module defines the configuration hierarchy for the pymorize application, using
``everett``'s ``~everett.manager.ConfigManager``. The configuration hierarchy is as follows (lowest to highest
priority):
    1. Hardcoded defaults
    2. User configuration file
    3. Run-specific configuration
    4. Environment variables
    5. Command-line switches

The configuration hierarchy is defined in the ``from_pymorize_cfg`` class method, and
cannot be modified outside the class. You should initialize a ``PymorizeConfigManager``
object (probably in your ``CMORizer``) and grab config values from it either by calling
it or by using the ``get`` method.

User Configuration File
-----------------------

You can define global configuration options in a user configuration file. The files found at these
locations will be used, in highest to lowest priority order:
    1. ``${PYMORIZE_CONFIG_FILE}``
    2. ``${XDG_CONFIG_HOME}/pymorize.yaml``
    3. ``${XDG_CONFIG_HOME}/pymorize/pymorize.yaml``
    4. ``~/.pymorize.yaml``

Note that the ``${XDG_CONFIG_HOME}`` environment variable defaults to ``~/.config`` if it is not set.

Configuration Options
---------------------

You can configuration the following:

.. autocomponentconfig:: pymorize.config.PymorizeConfig
   :case: upper
   :show-table:
   :namespace: pymorize

Usage
-----
Here are some examples of how to use the configuration manager::

    >>> pymorize_cfg = {}
    >>> config = PymorizeConfigManager.from_pymorize_cfg(pymorize_cfg)

    >>> engine = config("xarray_backend")
    >>> print(f"Using xarray backend: {engine}")
    'netcdf4'

    >>> parallel = config("parallel")
    >>> print(f"Running in parallel: {parallel}")
    True

You can define a user file at ``${XDG_CONFIG_DIR}/pymorize/pymorize.yaml``::

    >>> import pathlib
    >>> cfg_file = pathlib.Path("~/.config/pymorize/pymorize.yaml").expanduser()
    >>> cfg_file.mkdir(parents=True, exist_ok=True)
    >>> with open(cfg_file, "w") as f:
    ...     f.write("xarray_backend: zarr\nparallel: False\n")
    >>> config = PymorizeConfigManager.from_pymorize_cfg()
    >>> engine = config("xarray_backend")
    >>> print(f"Using xarray backend: {engine}")
    'zarr'
    

See Also
--------
- `Everett Documentation <https://everett.readthedocs.io/en/latest/>`_
"""

import os
import pathlib

from everett.ext.yamlfile import ConfigYamlEnv
from everett.manager import (ChoiceOf, ConfigDictEnv, ConfigManager,
                             ConfigOSEnv, Option, parse_bool)


class PymorizeConfig:
    class Config:
        xarray_backend = Option(
            default="netcdf4",
            doc="Which backend to use for xarray.",
            parser=ChoiceOf(str, choices=["netcdf4", "h5netcdf", "zarr"]),
        )
        parallel = Option(
            parser=parse_bool, default="True", doc="Whether to run in parallel."
        )
        parallel_backend = Option(default="dask", doc="Which parallel backend to use.")
        cluster_mode = Option(default="adapt", doc="Flexible dask cluster scaling")
        dask_scheduler = Option(
            default="local_process",
            doc="Dask scheduler to use.",
        )
        prefect_backend = Option(
            default="dask", doc="Which backend to use for Prefect."
        )
        pipeline_orchestrator = Option(
            default="prefect",
            doc="Which orchestrator to use.",
        )
        prefect_flow_runner = Option(
            default="local",
            doc="Which runner to use for Prefect flows.",
        )


class PymorizeConfigManager(ConfigManager):
    """
    Custom ConfigManager for Pymorize, with a predefined hierarchy and
    support for injecting run-specific configuration.
    """

    _XDG_CONFIG_HOME = os.environ.get("XDG_CONFIG_HOME", "~/.config")
    """str : The XDG configuration directory."""
    _CONFIG_FILES = [
        str(f)
        for f in [
            os.environ.get("PYMORIZE_CONFIG_FILE"),
            pathlib.Path(f"{_XDG_CONFIG_HOME}/pymorize.yaml").expanduser(),
            pathlib.Path(f"{_XDG_CONFIG_HOME}/pymorize/pymorize.yaml").expanduser(),
            pathlib.Path("~/.pymorize.yaml").expanduser(),
        ]
        if f
    ]
    """List[str] : The list of configuration files to check for user configuration."""

    @classmethod
    def from_pymorize_cfg(cls, run_specific_cfg=None):
        """
        Create a PymorizeConfigManager with the appropriate hierarchy.

        Parameters
        ----------
        run_specific_cfg : dict
            Optional. Overrides specific values for this run.
        """
        # Configuration higherarchy (highest to lowest priority):
        # 5. Command-line switches
        # Not implemented here
        # 4. Environment variables
        env_vars = ConfigOSEnv()
        # 3. Run-specific configuration
        run_specific = ConfigDictEnv(run_specific_cfg or {})

        # 2. User config file
        user_file = ConfigYamlEnv(cls._CONFIG_FILES)
        # 1. Hardcoded defaults
        # Handled by ``manager.with_options`` below

        # Combine everything into a new PymorizeConfigManager instance
        manager = cls(
            environments=[user_file, run_specific, env_vars],
        )
        return manager.with_options(PymorizeConfig())


if __name__ == "__main__":
