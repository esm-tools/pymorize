"""
Provides validation of user configuration files by checking against a schema.
"""

import importlib

from cerberus import Validator


class PipelineValidator(Validator):
    """
    Validator for pipeline configuration.

    See Also
    --------
    * https://cerberus-sanhe.readthedocs.io/customize.html#class-based-custom-validators
    """

    def _validate_is_qualname(self, is_qualname, field, value):
        """Test if a string is a Python qualname.

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}. This means that you can use a boolean value
        for the schema argument "is_qualname" in your rule definition.
        """
        if is_qualname and not isinstance(value, str):
            self._error(field, "Must be a string")
        if is_qualname:
            parts = value.split(".")
            module_name, attr_name = ".".join(parts[:-1]), parts[-1]
            try:
                module = importlib.import_module(module_name)
                if not hasattr(module, attr_name):
                    self._error(field, "Must be a valid Python qualname")
            except (ImportError, ModuleNotFoundError):
                self._error(field, "Must be a valid Python qualname")

    def _validate(self, document):
        super()._validate(document)
        if "steps" not in document and "uses" not in document:
            self._error(
                "document", 'At least one of "steps" or "uses" must be specified'
            )


PIPELINES_SCHEMA = {
    "pipelines": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {"type": "string", "required": False},
                "uses": {"type": "string", "excludes": "steps"},
                "steps": {
                    "type": "list",
                    "excludes": "uses",
                    "schema": {"type": "string", "is_qualname": True},
                },
            },
        },
    },
}
"""dict : Schema for validating pipelines configuration."""

PIPELINES_VALIDATOR = PipelineValidator(PIPELINES_SCHEMA)
"""Validator : Validator for pipelines configuration."""

RULES_SCHEMA = {
    "rules": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": {
                "name": {"type": "string", "required": False},
                "cmor_variable": {"type": "string", "required": True},
                "input_type": {
                    "type": "string",
                    "required": False,
                    "allowed": [
                        "xr.DataArray",
                        "xr.Dataset",
                    ],
                },
                "input_source": {
                    "type": "string",
                    "required": False,
                    "allowed": [
                        "xr_tutorial",
                    ],
                },
                "input_patterns": {
                    "type": "list",
                    "schema": {"type": "string"},
                    "required": True,
                },
                "enabled": {"type": "boolean", "required": False},
                "description": {"type": "string", "required": False},
                "pipelines": {
                    "type": "list",
                    # FIXME(PG): Should cross-check with pipelines.
                    "schema": {"type": "string"},
                },
                "cmor_units": {"type": "string", "required": False},
                # FIXME(PS): How is it currently defined?
                "model_units": {"type": "string", "required": False},
            },
        },
    },
}
"""dict : Schema for validating rules configuration."""
RULES_VALIDATOR = Validator(RULES_SCHEMA)
