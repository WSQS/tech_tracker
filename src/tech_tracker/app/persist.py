"""Application layer for persisting fetched items."""

from pathlib import Path
from typing import Union

from tech_tracker.app.youtube import fetch_youtube_videos_from_config
from tech_tracker.downloader import FeedDownloader
from tech_tracker.item_store import JsonItemStore
from tech_tracker.sources.youtube.to_items import youtube_videos_to_items


def fetch_and_persist_youtube_items(
    config_path: Union[str, Path],
    downloader: FeedDownloader,
    store: JsonItemStore,
) -> int:
    """Fetch YouTube videos from config and persist them to the store.
    
    Args:
        config_path: Path to the TOML configuration file.
        downloader: FeedDownloader implementation to use.
        store: JsonItemStore instance to save items to.
        
    Returns:
        Number of items written to the store.
    """
    # Fetch videos from YouTube sources
    videos_by_source_url = fetch_youtube_videos_from_config(config_path, downloader)
    
    # Convert videos to generic item structure
    items = youtube_videos_to_items(videos_by_source_url)
    
    # Save items to store
    store.save_many(items)
    
    return len(items)