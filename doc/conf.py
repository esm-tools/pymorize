# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import shutil
import sys

import sphinx.ext.apidoc

sys.path.insert(0, os.path.abspath("../src"))
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pymorize"
copyright = "2024, Paul Gierz"
author = "Paul Gierz"


modules = os.listdir("../src/")


# Ensure the API folder exists:
try:
    os.makedirs("api")
except FileExistsError:
    shutil.rmtree("api")
    os.makedirs("api")

with open("API.rst", "w") as rst:
    rst.write("==================\n")
    rst.write("Code Documentation\n")
    rst.write("==================\n")
    rst.write(".. toctree::\n")
    rst.write("   :glob:\n\n")
    rst.write("   api/*")

    for mod in sorted(modules):
        sphinx.ext.apidoc.main(
            [
                "--no-toc",
                "--module-first",
                "--output-dir",
                "api",
                "../src/" + mod,
            ]
        )
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.graphviz",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_rtd_theme",
    "sphinx_tabs.tabs",
    "sphinx_toolbox.collapse",
    "sphinx.ext.intersphinx",
]

# Strip the input promps for code cells when copying
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("http://docs.python.org/", None),
    "numpy": ("http://docs.scipy.org/doc/numpy/", None),
    "scipy": ("http://docs.scipy.org/doc/scipy/reference/", None),
    "matplotlib": ("http://matplotlib.sourceforge.net/", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/stable/", None),
    "xarray": ("http://xarray.pydata.org/en/stable/", None),
    "chemicals": ("https://chemicals.readthedocs.io/", None),
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
