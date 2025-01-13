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
object (probably in your ``CMORizer``) and grab config values from it by calling with the
config key as an argument.

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

You can configure the following:

.. autocomponentconfig:: pymorize.config.PymorizeConfig
   :case: upper
   :show-table:
   :namespace: pymorize

Usage
-----
Here are some examples of how to use the configuration manager::

    >>> pymorize_cfg = {}
    >>> config = PymorizeConfigManager.from_pymorize_cfg(pymorize_cfg)

    >>> engine = config("xarray_engine")
    >>> print(f"Using xarray backend: {engine}")
    Using xarray backend: netcdf4

    >>> parallel = config("parallel")
    >>> print(f"Running in parallel: {parallel}")
    Running in parallel: True

You can define a user file at ``${XDG_CONFIG_DIR}/pymorize/pymorize.yaml``::

    >>> import pathlib
    >>> import yaml
    >>> cfg_file = pathlib.Path("~/.config/pymorize/pymorize.yaml").expanduser()
    >>> cfg_file.parent.mkdir(parents=True, exist_ok=True)
    >>> cfg_to_dump = {"xarray_engine": "zarr"}
    >>> with open(cfg_file, "w") as f:
    ...     yaml.dump(cfg_to_dump, f)
    >>> config = PymorizeConfigManager.from_pymorize_cfg()
    >>> engine = config("xarray_engine")
    >>> print(f"Using xarray backend: {engine}")
    Using xarray backend: zarr

See Also
--------
- `Everett Documentation <https://everett.readthedocs.io/en/latest/>`_
"""

import os
import pathlib
from importlib.resources import files

from everett import InvalidKeyError
from everett.ext.yamlfile import ConfigYamlEnv
from everett.manager import (
    ChoiceOf,
    ConfigDictEnv,
    ConfigManager,
    ConfigOSEnv,
    Option,
    _get_component_name,
    parse_bool,
)

DIMENSIONLESS_MAPPING_TABLE = files("pymorize.data").joinpath(
    "dimensionless_mappings.yaml"
)


def _parse_bool(value):
    if isinstance(value, bool):
        return value
    return parse_bool(value)


class PymorizeConfig:
    class Config:
        dask_cluster = Option(
            default="local",
            doc="Dask cluster to use. See: https://docs.dask.org/en/stable/deploying.html",
            parser=ChoiceOf(
                str,
                choices=[
                    "local",
                    "slurm",
                ],
            ),
        )
        dask_cluster_scaling_mode = Option(
            default="adapt",
            doc="Flexible dask cluster scaling",
            parser=ChoiceOf(
                str,
                choices=[
                    "adapt",
                    "fixed",
                ],
            ),
        )
        dask_cluster_scaling_minimum_jobs = Option(
            parser=int,
            default=1,
            doc="Minimum number of jobs to create for Jobqueue-backed Dask Clusters (adaptive)",
        )
        dask_cluster_scaling_maximum_jobs = Option(
            parser=int,
            default=10,
            doc="Maximum number of jobs to create for Jobqueue-backed Dask Clusters (adaptive)",
        )
        dask_cluster_scaling_fixed_jobs = Option(
            parser=int,
            default=5,
            doc="Number of jobs to create for Jobqueue-backed Dask Cluster",
        )
        dimensionless_mapping_table = Option(
            parser=str,
            default=DIMENSIONLESS_MAPPING_TABLE,
            doc="Where the dimensionless unit mapping table is defined.",
        )
        enable_dask = Option(
            parser=_parse_bool,
            default="yes",
            doc="Whether to enable Dask-based processing",
        )
        enable_flox = Option(
            parser=_parse_bool,
            default="yes",
            doc="Whether to enable flox for group-by operation. See: https://flox.readthedocs.io/en/latest/",
        )
        parallel = Option(
            parser=_parse_bool, default="yes", doc="Whether to run in parallel."
        )
        parallel_backend = Option(default="dask", doc="Which parallel backend to use.")
        pipeline_workflow_orchestrator = Option(
            default="prefect",
            doc="Which workflow orchestrator to use for running pipelines",
            parser=ChoiceOf(
                str,
                choices=[
                    "native",
                    "prefect",
                ],
            ),
        )
        prefect_task_runner = Option(
            default="thread_pool",
            doc="Which runner to use for Prefect flows.",
            parser=ChoiceOf(
                str,
                choices=[
                    "thread_pool",
                    "dask",
                ],
            ),
        )
        quiet = Option(
            default=False, doc="Whether to suppress output.", parser=_parse_bool
        )
        raise_on_no_rule = Option(
            parser=_parse_bool,
            default="no",
            doc="Whether or not to raise an error if no rule is found for every single DataRequestVariable",
        )
        warn_on_no_rule = Option(
            parser=_parse_bool,
            default="yes",
            doc="Whether or not to issue a warning if no rule is found for every single DataRequestVariable",
        )
        xarray_engine = Option(
            default="netcdf4",
            doc="Which engine to use for xarray.",
            parser=ChoiceOf(
                str,
                choices=[
                    "netcdf4",
                    "h5netcdf",
                    "zarr",
                ],
            ),
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
        manager = manager.with_options(PymorizeConfig)
        return manager

    # NOTE(PG): Need to override this method, the original implementation in the parent class
    # explicitly uses ConfigManager (not cls) to create the clone instance.
    def clone(self):
        my_clone = PymorizeConfigManager(
            environments=list(self.envs),
            doc=self.doc,
            msg_builder=self.msg_builder,
            with_override=self.with_override,
        )
        my_clone.namespace = list(self.namespace)
        my_clone.bound_component = self.bound_component
        my_clone.bound_component_prefix = []
        my_clone.bound_component_options = self.bound_component_options

        my_clone.original_manager = self.original_manager

        return my_clone

    def __repr__(self) -> str:
        if self.bound_component:
            name = _get_component_name(self.bound_component)
            return f"<PymorizeConfigManager({name}): namespace:{self.get_namespace()}>"
        else:
            return f"<PymorizeConfigManager: namespace:{self.get_namespace()}>"

    def get(self, key, default=None, parser=None):
        """
        Get a configuration value by key, with a default value.

        Parameters
        ----------
        key : str
            The configuration key to get.
        default : Any
            The default value to return if the key is not found.
        parser : Callable
            Optional. A callable to parse the configuration value.

        Returns
        -------
        Any
            The configuration value.
        """
        try:
            return self(key, parser=parser)
        except InvalidKeyError:
            return default
