===============================================
``pymorize``: A Python package to simplify CMOR
===============================================

  ``pymorize`` is a Python package to simplify the standardization of output into the Climate Model Output Rewriter (CMOR) standard.

.. image:: https://github.com/esm-tools/pymorize/actions/workflows/CI-test.yaml/badge.svg
    :target: https://github.com/esm-tools/pymorize/actions/workflows/CI-test.yaml
.. image:: https://img.shields.io/pypi/v/pymorize.svg
    :target: https://pypi.python.org/pypi/pymorize
    :alt: Latest PyPI version
.. image:: https://readthedocs.org/projects/pymorize/badge/?version=latest
    :target: https://pymorize.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/github/license/esm-tools/pymorize
    :target: https://pymorize.readthedocs.io/en/latest/?badge=latest

------


  "Makes CMOR Simple" :-)

``pymorize`` is designed as a wrapper around various CMORization tools and NetCDF
command line tools to make reformatting data into CMIP6 compliant format as simple
and flexible as possible.

The package is designed to be modular and extensible, with a plugin system that allows
users to add their own subcommands to the main ``pymorize`` command line interface, as
well as including their own functionality to the standardization pipelines. The package is
also designed to be used as a library, with a simple API that allows users to use the
package in their own scripts.

To get started, you can install it via ``pip``::

    pip install git+https://github.com/esm-tools/pymorize

Then you can run the main command line interface. Start out by getting some help::

    pymorize --help


The most basic command you will run is::

    pymorize process <CONFIG_FILE>

More detailed install instructions can be found in the :ref:`installation` section, and usage
is summarized in the usage sections.


Licence
-------

``pymorize`` is licensed under the MIT license. See the LICENSE file for more details.

Contributors
------------

Thank you to all of our contributors!

.. image:: https://contrib.rocks/image?repo=esm-tools/pymorize
   :target: https://github.com/esm-tools/pymorize/graphs/contributors
   :alt: Contributors

Authors
-------

``pymorize`` was developed by the High Performance Computing and Data Processing group at
the Alfred Wegener Institute for Polar and Marine Research, Bremerhaven, Germany. It was
designed by `Paul Gierz <pgierz@awi.de>`_, and written by `Paul Gierz <pgierz@awi.de>`_ and
`Pavan Siligam <pavankumar.siligam@awi.de>`_.
