import sys

import rich_click as click

__version__ = "0.0.0"


@click.group()
@click.version_option(version=__version__)
def cli():
    return 0


def main():
    sys.exit(cli())


if __name__ == "__main__":
    main()
