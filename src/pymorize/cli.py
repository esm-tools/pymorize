import sys

import pkg_resources
import rich_click as click
from click_loguru import ClickLoguru
from loguru import logger
from rich.logging import RichHandler

from . import _version

logger.configure(handlers=[{"sink": RichHandler(), "format": "{message}"}])

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


# @pymorize_cli_group
@click_loguru.logging_options
@click.group(name="pymorize", help="Pymorize - Makes CMOR Simple (or Great Again!)")
@click_loguru.stash_subcommand()
@click.version_option(version=VERSION, prog_name=NAME)
def cli(verbose, quiet, logfile, profile_mem):
    return 0


def main():
    for entry_point_name, entry_point in find_subcommands().items():
        cli.add_command(entry_point["callable"], name=entry_point_name)
    cli()


if __name__ == "__main__":
    sys.exit(main())
