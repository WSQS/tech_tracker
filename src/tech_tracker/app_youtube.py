"""YouTube application layer for fetching videos from configuration."""

from pathlib import Path
from typing import Any, Dict, List, Union

from tech_tracker.config import load_sources_from_toml
from tech_tracker.downloader import FeedDownloader
from tech_tracker.youtube_channel import extract_channel_id_from_youtube_url
from tech_tracker.youtube_fetch import fetch_youtube_videos


def fetch_youtube_videos_from_config(
    config_path: Union[str, Path],
    downloader: FeedDownloader
) -> Dict[str, List[Dict[str, Any]]]:
    """Fetch YouTube videos from all YouTube sources in a configuration file.
    
    Args:
        config_path: Path to the TOML configuration file.
        downloader: FeedDownloader implementation to use.
        
    Returns:
        Dictionary mapping YouTube source URLs to their video lists.
        Only sources with type="youtube" and extractable channel IDs are included.
    """
    # Load sources from configuration
    sources = load_sources_from_toml(config_path)
    
    # Filter for YouTube sources only
    youtube_sources = [
        source for source in sources 
        if source.get("type") == "youtube"
    ]
    
    results: Dict[str, List[Dict[str, Any]]] = {}
    
    for source in youtube_sources:
        url = source.get("url")
        if not url:
            continue  # Skip sources without URL
            
        # Extract channel ID from URL
        channel_id = extract_channel_id_from_youtube_url(url)
        if channel_id is None:
            continue  # Skip sources where channel ID cannot be extracted
            
        # Fetch videos for this channel
        try:
            videos = fetch_youtube_videos(channel_id, downloader)
            results[url] = videos
        except Exception:
            # Skip sources that fail to fetch, but continue with others
            continue
    
    return results