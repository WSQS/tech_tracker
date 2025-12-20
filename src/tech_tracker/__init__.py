"""Tech Tracker - A tool for tracking and managing tech information."""

__version__ = "0.1.0"

from .item import Item

__all__ = ["Item"]


def ping() -> str:
    """Simple ping function for testing purposes.
    
    Returns:
        str: The string "pong" to verify the module is working.
    """
    return "pong"