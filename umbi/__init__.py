import os
import tomllib

from .logger import set_log_level, setup_logging
from .version import __toolname__, __version__, __format_version__, __format_revision__

# import core submodules (ats is imported lazily to avoid circular dependency)
from . import binary, io, vectors
