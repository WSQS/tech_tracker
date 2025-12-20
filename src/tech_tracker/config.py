"""Configuration module for loading and parsing TOML files."""

from pathlib import Path
from typing import Any, Dict, List, Union

import tomllib


def load_sources_from_toml(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load sources configuration from a TOML file.
    
    Args:
        path: Path to the TOML configuration file.
        
    Returns:
        List of normalized source dictionaries, each containing:
        - type: str (one of "rss", "youtube", "bilibili", "webpage")
        - url: str
        - title: str or None
        
    Raises:
        ValueError: If the configuration is invalid or missing required fields.
        FileNotFoundError: If the specified file does not exist.
        tomllib.TOMLDecodeError: If the TOML file is malformed.
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with path.open("rb") as f:
        data = tomllib.load(f)
    
    # Check if sources exists and is a list
    if "sources" not in data:
        raise ValueError("Missing 'sources' section in configuration")
    
    sources = data["sources"]
    if not isinstance(sources, list):
        raise ValueError("'sources' must be a list")
    
    if not sources:
        return []
    
    # Valid source types
    valid_types = {"rss", "youtube", "bilibili", "webpage"}
    
    normalized_sources = []
    
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Source at index {i} must be a table")
        
        # Check required fields
        if "type" not in source:
            raise ValueError(f"Source at index {i} missing required field 'type'")
        
        if "url" not in source:
            raise ValueError(f"Source at index {i} missing required field 'url'")
        
        source_type = source["type"]
        source_url = source["url"]
        
        # Validate type field
        if not isinstance(source_type, str):
            raise ValueError(f"Source at index {i}: 'type' must be a string")
        
        if source_type not in valid_types:
            raise ValueError(
                f"Source at index {i}: 'type' must be one of {valid_types}, "
                f"got '{source_type}'"
            )
        
        # Validate url field
        if not isinstance(source_url, str):
            raise ValueError(f"Source at index {i}: 'url' must be a string")
        
        if not source_url.strip():
            raise ValueError(f"Source at index {i}: 'url' cannot be empty")
        
        # Validate optional title field
        title = source.get("title")
        if title is not None and not isinstance(title, str):
            raise ValueError(f"Source at index {i}: 'title' must be a string or None")
        
        # Create normalized source
        normalized_source = {
            "type": source_type,
            "url": source_url,
            "title": title,
        }
        
        normalized_sources.append(normalized_source)
    
    return normalized_sources