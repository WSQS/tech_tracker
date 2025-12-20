"""Update tracking application layer."""

from pathlib import Path
from typing import Any, Dict, List, Union

from tech_tracker.app_youtube import fetch_youtube_videos_from_config
from tech_tracker.downloader import FeedDownloader
from tech_tracker.item_diff import diff_new_items
from tech_tracker.item_store import JsonItemStore
from tech_tracker.sources.youtube.to_items import youtube_videos_to_items


def fetch_youtube_new_items(
    config_path: Union[str, Path],
    downloader: FeedDownloader,
    store: JsonItemStore,
) -> List[Dict[str, Any]]:
    """Fetch YouTube videos and return only new items compared to store.
    
    This function:
    1. Loads existing items from store
    2. Fetches YouTube videos from config
    3. Converts videos to items
    4. Computes diff to find new items
    5. Saves all fetched items to store
    6. Returns only the new items
    
    Args:
        config_path: Path to the TOML configuration file.
        downloader: FeedDownloader implementation to use.
        store: JsonItemStore instance for persistence.
        
    Returns:
        List of new item dictionaries that weren't in the store before.
    """
    # 1) Load existing items from store
    old_items = store.load_all()
    
    # 2) Fetch YouTube videos from config
    videos_by_source_url = fetch_youtube_videos_from_config(config_path, downloader)
    
    # 3) Convert videos to items
    new_items = youtube_videos_to_items(videos_by_source_url)
    
    # 4) Compute diff to find new items
    added_items = diff_new_items(old_items, new_items)
    
    # 5) Save all fetched items to store (not just new ones)
    store.save_many(new_items)
    
    # 6) Return only the new items
    return added_items