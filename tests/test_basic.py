"""Basic tests for tech_tracker module."""

import pytest
from tech_tracker import ping, __version__


def test_module_import():
    """Test that the module can be imported."""
    import tech_tracker
    assert tech_tracker is not None


def test_ping_function():
    """Test the ping function returns expected result."""
    result = ping()
    assert result == "pong"


def test_version():
    """Test that version is defined."""
    assert __version__ == "0.1.0"
    assert isinstance(__version__, str)