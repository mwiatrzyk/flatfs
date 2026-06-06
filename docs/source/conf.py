# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import doctest
import pathlib
import sys

project_root = pathlib.Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

import flatfs

project = "FlatFS"
copyright = "2026, Maciej Wiatrzyk"
author = "Maciej Wiatrzyk <maciej.wiatrzyk@gmail.com>"
release = flatfs.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_theme_options = {"version_selector": True}


# -- Extension configuration

# sphinx.ext.intersphinx
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# sphinx.ext.doctest
doctest_default_flags = doctest.ELLIPSIS | doctest.DONT_ACCEPT_TRUE_FOR_1
