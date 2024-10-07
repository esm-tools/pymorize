import os
import pathlib
import sys
from importlib import resources

import pkg_resources
import rich_click as click
import yaml
from click_loguru import ClickLoguru
from dask.distributed import Client
from rich.traceback import install as rich_traceback_install
from streamlit.web import cli as stcli

from . import _version, dev_utils
from .cmorizer import CMORizer
from .logging import logger
from .ssh_tunnel import ssh_tunnel_cli
from .validate import PIPELINES_VALIDATOR, RULES_VALIDATOR

MAX_FRAMES = int(os.environ.get("PYMORIZE_ERROR_MAX_FRAMES", 3))
"""
str: The maximum number of frames to show in the traceback if there is an error. Default to 3
"""
# install rich traceback
rich_traceback_install(show_locals=True, max_frames=MAX_FRAMES)

VERSION = _version.get_versions()["version"]

# global constants
LOG_FILE_RETENTION = 3
NAME = "pymorize"
# define the CLI
click_loguru = ClickLoguru(
    NAME,
    VERSION,
    retention=LOG_FILE_RETENTION,
    # log_dir_parent="tests/data/logs",
    timer_log_level="info",
)


# FIXME(PG): Doesn't work as intended :-(
def pymorize_cli_group(func):
    """
    Decorator to add the click_loguru logging options to a click group
    """
    func = click_loguru.logging_options(func)
    func = click.group()(func)
    func = click_loguru.stash_subcommand()(func)
    func = click.version_option(
        version=VERSION, prog_name="Pymorize - Make CMOR Simple"
    )(func)
    return func


def find_subcommands():
    """
    Finds CLI Subcommands for installed pymorize plugins
    """
    discovered_subcommands = {
        entry_point.name: {
            "plugin_name": entry_point.module_name.split(".")[0],
            "callable": entry_point.load(),
        }
        for entry_point in pkg_resources.iter_entry_points("pymorize.cli_subcommands")
    }
    return discovered_subcommands


@click_loguru.logging_options
@click.group(name="pymorize", help="Pymorize - Makes CMOR Simple (or Great Again!)")
@click_loguru.stash_subcommand()
@click.version_option(version=VERSION, prog_name=NAME)
def cli(verbose, quiet, logfile, profile_mem):
    return 0


################################################################################
################################################################################
################################################################################

################################################################################
# Direct Commands
################################################################################


@cli.command()
@click_loguru.init_logger()
@click.argument("config_file", type=click.Path(exists=True))
def process(config_file):
    logger.info(f"Processing {config_file}")
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)
    cmorizer = CMORizer.from_dict(cfg)
    client = Client(cmorizer._cluster)
    cmorizer.process()


@cli.command()
@click_loguru.init_logger()
def table_explorer():
    logger.info("Launching table explorer...")
    with resources.path("pymorize", "webapp.py") as webapp_path:
        sys.argv = ["streamlit", "run", str(webapp_path)]
        stcli.main()


################################################################################
# SUBCOMMANDS
################################################################################
@click_loguru.logging_options
@click.group()
@click_loguru.stash_subcommand()
@click.version_option(version=VERSION, prog_name=NAME)
def validate(verbose, quiet, logfile, profile_mem):
    return 0


@click_loguru.logging_options
@click.group()
@click_loguru.stash_subcommand()
@click.version_option(version=VERSION, prog_name=NAME)
def develop(verbose, quiet, logfile, profile_mem):
    return 0


################################################################################
################################################################################
################################################################################

################################################################################
# COMMANDS FOR develop
################################################################################


@develop.command()
@click_loguru.logging_options
@click_loguru.init_logger()
@click.argument("directory", type=click.Path(exists=True))
@click.argument("output_file", type=click.File("w"), required=False, default=None)
def ls(directory, output_file, verbose, quiet, logfile, profile_mem):
    yaml_str = dev_utils.ls_to_yaml(directory)
    # Append to beginning of output file
    if output_file is not None:
        output_file.write(f"# Created with: pymorize develop ls {directory}\n")
        output_file.write(yaml_str)
    return 0


################################################################################
################################################################################
################################################################################

################################################################################
# COMMANDS FOR validate
################################################################################


@validate.command()
@click_loguru.logging_options
@click_loguru.init_logger()
@click.argument("config_file", type=click.Path(exists=True))
def config(config_file, verbose, quiet, logfile, profile_mem):
    logger.info(f"Checking if a CMORizer can be built from {config_file}")
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)
        if "pipelines" in cfg:
            pipelines = cfg["pipelines"]
            PIPELINES_VALIDATOR.validate({"pipelines": pipelines})
        if "rules" in cfg:
            rules = cfg["rules"]
            RULES_VALIDATOR.validate({"rules": rules})
        if not PIPELINES_VALIDATOR.errors and not RULES_VALIDATOR.errors:
            logger.success(
                f"Configuration {config_file} is valid for both rules and pipelines!"
            )
        for key, error in {
            **PIPELINES_VALIDATOR.errors,
            **RULES_VALIDATOR.errors,
        }.items():
            logger.error(f"{key}: {error}")


@validate.command()
@click_loguru.logging_options
@click_loguru.init_logger()
@click.argument("config_file", type=click.Path(exists=True))
@click.argument("table_name", type=click.STRING)
def table(config_file, table_name, verbose, quiet, logfile, profile_mem):
    logger.info(f"Processing {config_file}")
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)
        cmorizer = CMORizer.from_dict(cfg)
        cmorizer.check_rules_for_table(table_name)


@validate.command()
@click_loguru.logging_options
@click_loguru.init_logger()
@click.argument("config_file", type=click.Path(exists=True))
@click.argument("output_dir", type=click.STRING)
def directory(config_file, output_dir, verbose, quiet, logfile, profile_mem):
    logger.info(f"Processing {config_file}")
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)
        cmorizer = CMORizer.from_dict(cfg)
        cmorizer.check_rules_for_output_dir(output_dir)


################################################################################
################################################################################
################################################################################


def main():
    for entry_point_name, entry_point in find_subcommands().items():
        cli.add_command(entry_point["callable"], name=entry_point_name)
    cli.add_command(validate)
    cli.add_command(develop)
    cli.add_command(ssh_tunnel_cli, name="ssh-tunnel")
    cli(auto_envvar_prefix="PYMORIZE")


if __name__ == "__main__":
    sys.exit(main())
