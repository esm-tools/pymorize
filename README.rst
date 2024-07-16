``pymorize``: A Python package to simplify do CMOR
==================================================

  ``pymorize`` is a Python package to simplify the standardization of output into the Climate Model Output Rewriter (CMOR) standard.
.. image:: https://github.com/esm-tools/pymorize/actions/workflows/CI-test.yaml/badge.svg
    :target: https://github.com/esm-tools/pymorize/actions/workflows/CI-test.yaml
.. image:: https://img.shields.io/pypi/v/pymorize.svg
    :target: https://pypi.python.org/pypi/pymorize
    :alt: Latest PyPI version
.. image:: https://readthedocs.org/projects/pymorize/badge/?version=latest
    :target: https://pymorize.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/github/license/pgierz/pymorize
    :target: https://pymorize.readthedocs.io/en/latest/?badge=latest
------


It "Makes CMOR Simple" :-) ``pymorize`` is designed as a wrapper around various CMORization tools and NetCDF command line tools to make reformatting data into CMIP6 compliant format as simple and flexible as possible.

The package is designed to be modular and extensible, with a plugin system that allows users to add their own subcommands to the main `pymorize` command line interface. The package is also designed to be used as a library, with a simple API that allows users to use the package in their own scripts. 

To get started, you can install it via ``pip``::
  
    pip install git+https://github.com/pgierz/pymorize
  
Then you can run the main command line interface. Start out by getting some help::
  
    pymorize --help

More detailed install instructions can be found in the :ref:`installation` section.


Licence
-------

``pymorize`` is licensed under the MIT license. See the LICENSE file for more details.

Authors
-------

`pymorize` was written by `Paul Gierz <pgierz@awi.de>`_.
