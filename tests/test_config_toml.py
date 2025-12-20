"""Tests for TOML configuration loading."""

import pytest
from pathlib import Path

from tech_tracker.config import load_sources_from_toml


def test_load_sources_normal(tmp_path: Path) -> None:
    """Test normal parsing of sources with and without titles."""
    toml_content = """[[sources]]
type = "rss"
url = "https://example.com/rss.xml"
title = "Example RSS"

[[sources]]
type = "youtube"
url = "https://youtube.com/channel/UC123"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    sources = load_sources_from_toml(config_file)
    
    assert len(sources) == 2
    
    # First source with title
    assert sources[0]["type"] == "rss"
    assert sources[0]["url"] == "https://example.com/rss.xml"
    assert sources[0]["title"] == "Example RSS"
    
    # Second source without title
    assert sources[1]["type"] == "youtube"
    assert sources[1]["url"] == "https://youtube.com/channel/UC123"
    assert sources[1]["title"] is None


def test_load_sources_missing_type(tmp_path: Path) -> None:
    """Test error when source is missing type field."""
    toml_content = """[[sources]]
url = "https://example.com/rss.xml"
title = "Example RSS"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    with pytest.raises(ValueError, match="missing required field 'type'"):
        load_sources_from_toml(config_file)


def test_load_sources_missing_url(tmp_path: Path) -> None:
    """Test error when source is missing url field."""
    toml_content = """[[sources]]
type = "rss"
title = "Example RSS"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    with pytest.raises(ValueError, match="missing required field 'url'"):
        load_sources_from_toml(config_file)


def test_load_sources_invalid_type(tmp_path: Path) -> None:
    """Test error when source type is not in allowed values."""
    toml_content = """[[sources]]
type = "invalid"
url = "https://example.com/rss.xml"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    with pytest.raises(ValueError, match="'type' must be one of"):
        load_sources_from_toml(config_file)


def test_load_sources_empty_url(tmp_path: Path) -> None:
    """Test error when source url is empty."""
    toml_content = """[[sources]]
type = "rss"
url = ""
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    with pytest.raises(ValueError, match="'url' cannot be empty"):
        load_sources_from_toml(config_file)


def test_load_sources_missing_sources_section(tmp_path: Path) -> None:
    """Test error when sources section is missing."""
    toml_content = """[other_section]
key = "value"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    with pytest.raises(ValueError, match="Missing 'sources' section"):
        load_sources_from_toml(config_file)


def test_load_sources_not_a_list(tmp_path: Path) -> None:
    """Test error when sources is not a list."""
    toml_content = """[sources]
type = "rss"
url = "https://example.com/rss.xml"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    with pytest.raises(ValueError, match="'sources' must be a list"):
        load_sources_from_toml(config_file)


def test_load_sources_file_not_found() -> None:
    """Test error when configuration file does not exist."""
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_sources_from_toml("nonexistent.toml")


def test_load_sources_empty_sources(tmp_path: Path) -> None:
    """Test handling of empty sources list."""
    toml_content = """sources = []
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    sources = load_sources_from_toml(config_file)
    assert sources == []


def test_load_sources_all_valid_types(tmp_path: Path) -> None:
    """Test all valid source types."""
    toml_content = """[[sources]]
type = "rss"
url = "https://example.com/rss.xml"

[[sources]]
type = "youtube"
url = "https://youtube.com/channel/UC123"

[[sources]]
type = "bilibili"
url = "https://bilibili.com/video/BV123"

[[sources]]
type = "webpage"
url = "https://example.com/page"
"""
    
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)
    
    sources = load_sources_from_toml(config_file)
    
    assert len(sources) == 4
    assert sources[0]["type"] == "rss"
    assert sources[1]["type"] == "youtube"
    assert sources[2]["type"] == "bilibili"
    assert sources[3]["type"] == "webpage"
    
    for source in sources:
        assert source["title"] is None
        assert isinstance(source["url"], str)
        assert len(source["url"]) > 0