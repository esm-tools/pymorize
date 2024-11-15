from everett.ext.yamlfile import ConfigYamlEnv
from everett.manager import ConfigDictEnv, ConfigManager, ConfigOSEnv

DEFAULTS = {
    "parallel": True,
    "parallel.backend": "dask",
    "cluster_mode": "adapt",
    "minimum_jobs": 1,
    "maximum_jobs": 10,
    "fixed_jobs": 5,
    "use_flox": False,
    "raise_on_no_rule": False,
    "warn_on_no_rule": True,
    "raise_on_multiple_rules": True,
    "xarray_netcdf_backend": "netcdf4",
}


class PymorizeConfigManager(ConfigManager):
    """
    Custom ConfigManager for Pymorize, with a predefined hierarchy and
    support for injecting run-specific configuration.
    """

    @classmethod
    def from_pymorize_cfg(cls, run_specific_cfg=None):
        """
        Create a PymorizeConfigManager with the appropriate hierarchy.

        Args:
            run_specific_cfg (dict): Optional. Overrides specific values for this run.
        """
        # 1. Hardcoded defaults
        hard_defaults = ConfigDictEnv(
            DEFAULTS,
            description="Hardcoded defaults for Pymorize",
        )

        # 2. User config file
        user_file = ConfigYamlEnv(filename="~/.config/pymorize.yaml")

        # 3. Run-specific configuration
        run_specific = ConfigDictEnv(run_specific_cfg or {})

        # 4. Environment variables
        env_vars = ConfigOSEnv(namespace="PYMORIZE")

        # Combine everything into a new PymorizeConfigManager instance
        return cls(environments=[hard_defaults, user_file, run_specific, env_vars])

    def get(self, key, default=None, parser=None):
        """
        Retrieves the value for a key, with optional default and parser.

        Args:
            key (str): The configuration key to retrieve.
            default (Any): The default value to return if the key is not found.
            parser (callable): Optional. A function to parse the value.

        Returns:
            Any: The retrieved and optionally parsed value.
        """
        try:
            value = self(key, parser=parser)  # Use Everett's `__call__` under the hood
        except KeyError:
            value = default
        return value
