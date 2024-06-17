.. pymorize documentation master file, created by
   sphinx-quickstart on Fri Jun 14 09:55:12 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pymorize's documentation!
====================================

.. image:: https://img.shields.io/pypi/v/pymorize.svg
    :target: https://pypi.python.org/pypi/pymorize
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/pymorize.svg

.. image:: https://img.shields.io/pypi/l/pymorize.svg

``pymorize`` is a Python package that should "Make CMOR Simple". It is designed as a wrapper around various CMORization tools and NetCDF command line tools to make reformatting data into CMIP6 compliant format as simple and flexible as possible.

The package is designed to be modular and extensible, with a plugin system that allows users to add their own subcommands to the main `pymorize` command line interface. The package is also designed to be used as a library, with a simple API that allows users to use the package in their own scripts. 

To get started, you can install it via ``pip``::
  
    pip install pymorize
  
Then you can run the main command line interface. Start out by getting some help::
  
    pymorize --help

More detailed install instructions can be found in the :ref:`installation` section. ``pymorize`` ships with a *generic* subcommand that can be used to CMORize data not covered by a specific subcommand. Here is an example usage::

    pymorize generic -i input.nc -o output.nc -v tas -f Amon -m CMIP6 -e historical -r r1i1p1f1


Contents
========

.. toctree::
   :maxdepth: 2
    
   including_subcommand_plugins
   API



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
