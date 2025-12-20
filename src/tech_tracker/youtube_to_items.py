"""YouTube videos to generic items conversion utilities."""

from typing import Any, Dict, List


def youtube_videos_to_items(videos_by_source_url: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Convert YouTube videos to generic item structure.
    
    Args:
        videos_by_source_url: Dictionary mapping source URLs to video lists.
        
    Returns:
        List of item dictionaries with the following structure:
        - item_id: str (video_id from YouTube)
        - source_type: str (always "youtube")
        - source_url: str (the source URL from the input dict)
        - title: str (video title)
        - link: str (video link)
        - published: datetime (UTC timezone-aware)
    """
    items = []
    
    for source_url, videos in videos_by_source_url.items():
        for video in videos:
            # Extract required fields from video
            video_id = video.get("video_id")
            title = video.get("title")
            link = video.get("link")
            published = video.get("published")
            
            # Skip if required fields are missing
            if not all([video_id, title, link, published]):
                continue
            
            # Create item with mapped fields
            item = {
                "item_id": video_id,
                "source_type": "youtube",
                "source_url": source_url,
                "title": title,
                "link": link,
                "published": published,
            }
            
            items.append(item)
    
    return items