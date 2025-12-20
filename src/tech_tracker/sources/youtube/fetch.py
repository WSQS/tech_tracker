"""YouTube video fetching functionality."""

from typing import Any, Dict, List

from tech_tracker.downloader import FeedDownloader
from tech_tracker.youtube_rss import build_youtube_feed_url, parse_youtube_feed


def fetch_youtube_videos(
    channel_id: str, 
    downloader: FeedDownloader
) -> List[Dict[str, Any]]:
    """Fetch YouTube videos from a channel using the provided downloader.
    
    Args:
        channel_id: YouTube channel ID.
        downloader: FeedDownloader implementation to use.
        
    Returns:
        List of video entries, each containing:
        - video_id: str (YouTube video ID)
        - title: str (Video title)
        - link: str (Video URL)
        - published: datetime (timezone-aware, UTC)
        
    Raises:
        ValueError: If channel_id is invalid or fetching fails.
    """
    # Build the feed URL
    url = build_youtube_feed_url(channel_id)
    
    # Fetch the XML content
    xml = downloader.fetch_text(url)
    
    # Parse the XML and return videos
    return parse_youtube_feed(xml)