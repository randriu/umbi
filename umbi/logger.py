"""Logging setup for the umbi package."""

import logging


def setup_logging(level=logging.INFO):
    """Set up logging for the umbi package."""
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger = logging.getLogger("umbi")
    logger.addHandler(handler)
    logger.setLevel(level)


def set_log_level(level=logging.INFO):
    """Set the logging level for the umbi package."""
    logger = logging.getLogger("umbi")
    logger.setLevel(level)
