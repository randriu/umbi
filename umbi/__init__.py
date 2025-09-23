import os
import tomllib

from . import binary, io, vectors
from .logger import set_log_level, setup_logging


def get_pyproject_attribute(attribute, default, section="project"):
    """Read an attribute from pyproject.toml."""
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
            section_data = data.get(section, {})
            return section_data.get(attribute, default)
    except (FileNotFoundError, KeyError):
        return default


__toolname__ = get_pyproject_attribute("name", "unknown")
__version__ = get_pyproject_attribute("version", "unknown")
__format_version__ = get_pyproject_attribute("format_version", 0, "tool.umbi")
__format_revision__ = get_pyproject_attribute("format_revision", 1, "tool.umbi")
