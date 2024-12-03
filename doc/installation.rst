============
Installation
============

The package can be installed in several ways:

From PyPI
---------

This is the most straightforward way to install the package if you don't need to modify the source code. Just run::

    pip install pymorize

You can also install the latest version from the repository by running::

  pip install git+https://github.com/esm-tools/pymorize.git

If you want to ensure an isolated install and make sure nothing conflicts with other packages you have, and you **do not want to change source code**, you can have a look at
`pipx <https://pipx.pypa.io/stable/>`_.

From source
-----------

If you want to modify the source code, you can install the package by cloning the repository and running::

    git clone https://esm-tools/pymorize.git
    cd pymorize
    python -m pip install -e .
