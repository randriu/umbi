
import os

import tomllib

from .io import *
from .index import UmbIndex
from .logging import setup_logging,set_log_level
from .umb import read_umb, write_umb, ExplicitUmb


def get_pyproject_attribute(attribute, default):
    """Read an attribute from pyproject.toml."""
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    try:
        with open(pyproject_path, "rb") as f:
            project_data = tomllib.load(f)["project"]
            return project_data.get(attribute)
    except (FileNotFoundError, KeyError):
        return default


__toolname__ = get_pyproject_attribute("name", "unknown")
__version__ = get_pyproject_attribute("version", "0.0.0")
__format_version__ = get_pyproject_attribute("format_version", 0)
__format_revision__ = get_pyproject_attribute("format_revision", 1)
