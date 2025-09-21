import os
import tomllib

from .index import UmbIndex
from .logger import set_log_level, setup_logging
from .umb import ExplicitUmb, read_umb, write_umb

__all__ = [
    "set_log_level",
    "setup_logging",
    "UmbIndex",
    "ExplicitUmb",
    "read_umb",
    "write_umb",
]

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
__version__ = get_pyproject_attribute("version", "unknown")
__format_version__ = get_pyproject_attribute("format_version", 0)
__format_revision__ = get_pyproject_attribute("format_revision", 1)
