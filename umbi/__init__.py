import logging
import os

import tomli

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s - %(message)s")

from .explicit_ats import ExplicitAts
from .io_bytes import *
from .io_json import *
from .io_tar import *
from .io_umb import *

# from .simple_ats import SimpleAts


def get_pyproject_attribute(attribute, default):
    """Read an attribute from pyproject.toml."""
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    try:
        with open(pyproject_path, "rb") as f:
            project_data = tomli.load(f)["project"]
            return project_data.get(attribute)
    except (FileNotFoundError, KeyError):
        return default


__toolname__ = get_pyproject_attribute("name", "unknown")
__version__ = get_pyproject_attribute("version", "0.0.0")

# TODO move to config file
__format_version__ = 0
__format_revision__ = 1
