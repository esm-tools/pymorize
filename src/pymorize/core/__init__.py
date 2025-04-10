"""
Core functionality for the pymorize package.

This module provides the core components needed for CMORizing datasets
according to CMIP standards.
"""

# Cluster support
from .cluster import (
    CLUSTER_ADAPT_SUPPORT,
    CLUSTER_MAPPINGS,
    CLUSTER_SCALE_SUPPORT,
    DaskContext,
    set_dashboard_link,
)

# Main CMORizer class
from .cmorizer import CMORizer

# Configuration and validation
from .config import PymorizeConfig, PymorizeConfigManager
from .controlled_vocabularies import ControlledVocabularies
from .factory import MetaFactory, create_factory

# File handling and utilities
from .filecache import fc
from .logging import add_report_logger, logger
from .pipeline import Pipeline

# Core components for defining and running pipelines
from .rule import Rule
from .ssh_tunnel import ssh_tunnel_cli
from .utils import wait_for_workers
from .validate import GENERAL_VALIDATOR, PIPELINES_VALIDATOR, RULES_VALIDATOR

__all__ = [
    # Main class
    "CMORizer",
    # Core components
    "Rule",
    "Pipeline",
    # Configuration
    "PymorizeConfig",
    "PymorizeConfigManager",
    # Validation
    "GENERAL_VALIDATOR",
    "PIPELINES_VALIDATOR",
    "RULES_VALIDATOR",
    "ControlledVocabularies",
    # Utilities
    "fc",
    "ssh_tunnel_cli",
    "logger",
    "add_report_logger",
    "create_factory",
    "MetaFactory",
    "wait_for_workers",
    # Cluster
    "DaskContext",
    "CLUSTER_MAPPINGS",
    "CLUSTER_ADAPT_SUPPORT",
    "CLUSTER_SCALE_SUPPORT",
    "set_dashboard_link",
]
