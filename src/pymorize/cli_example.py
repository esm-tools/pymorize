"""An extremely simple command-line application."""

# standard library imports
import array
import sys
from time import sleep

# third-party imports
import rich_click as click
# module imports
from click_loguru import ClickLoguru

# self imports
from .logging import logger
from .other_module import other_module_levels

# global constants
LOG_FILE_RETENTION = 3
VERSION = "0.4.0"
NAME = "simple"

# define the CLI
click_loguru = ClickLoguru(
    NAME,
    VERSION,
    retention=LOG_FILE_RETENTION,
    log_dir_parent="tests/data/logs",
    timer_log_level="info",
)


@click_loguru.logging_options
@click.group()
@click_loguru.stash_subcommand()
@click.option(
    "-e",
    "--extra",
    is_flag=True,
    show_default=True,
    default=False,
    help="An extra global option.",
    callback=click_loguru.user_global_options_callback,
)
@click.version_option(version=VERSION, prog_name=NAME)
def cli(verbose, quiet, logfile, profile_mem, extra):
    """simple -- a simple cli function with logging by loguru."""
    unused_str = (
        f"verbose: {verbose} quiet: {quiet}"
        + f" logfile: {logfile} profile_mem: {profile_mem} extra{extra}"
    )


@cli.command()
@click_loguru.init_logger()
def levels():
    """Log at different severity levels."""
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    state = click_loguru.get_global_options()
    print(f"logfile_path: {state.logfile_path}")


@cli.command()
@click_loguru.init_logger()
def other_module():
    """Log from another module."""
    other_module_levels()
    state = click_loguru.get_global_options()
    print(f"logfile_path: {state.logfile_path}")


@cli.command()
@click_loguru.init_logger()
def show_context():
    "Print value of global quiet option."
    state = click_loguru.get_global_options()
    print(f"verbose: {state.verbose}")
    print(f"quiet: {state.quiet}")
    print(f"logfile: {state.logfile}")
    if state.subcommand is None:
        print("No subcommand")
    else:
        print(f'Subcommand: "{state.subcommand}"')
    if state.logfile_handler_id is None:
        print("No logfile handler.")
    else:
        print(f'Logfile path: "{state.logfile_path}"')
    print(f"{state}")


@cli.command()
@click_loguru.init_logger(logfile=False)
def quiet_value():
    "Print value of global quiet option."
    state = click_loguru.get_global_options()
    print(f"{state.quiet:d}", end="")


@cli.command()
@click_loguru.init_logger(logfile=False)
def extra_value():
    "Print value of global quiet option."
    user_options = click_loguru.get_user_global_options()
    print(f"{user_options['extra']:d}", end="")


@cli.command()
@click_loguru.init_logger()
@click_loguru.log_elapsed_time(level="info")
def log_elapsed_time():
    """Print elapsed time in command."""
    click_loguru.elapsed_time("first")
    sleep(1)
    click_loguru.elapsed_time("second")
    sleep(2)
    click_loguru.elapsed_time(None)


@cli.command()
@click_loguru.init_logger()
@click_loguru.log_peak_memory_use(level="info")
@click.argument("alloc_size", type=int)
def log_memory_use(alloc_size):
    """Print elapsed time in command."""
    arr = array.array("b")
    for unused_i in range(alloc_size * 1024 * 1024):
        arr.append(0)


def main():
    return sys.exit(cli())


if __name__ == "__main__":
    main()
