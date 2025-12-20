"""YouTube channel ID extraction utilities."""

import re
from typing import Optional
from urllib.parse import urlparse


def extract_channel_id_from_youtube_url(url: str) -> Optional[str]:
    """Extract YouTube channel ID from a YouTube URL.
    
    This function only supports URLs in the format:
    - https://www.youtube.com/channel/<CHANNEL_ID>
    - https://youtube.com/channel/<CHANNEL_ID>
    - https://www.youtube.com/channel/<CHANNEL_ID>/
    - https://youtube.com/channel/<CHANNEL_ID>/
    
    Args:
        url: YouTube URL to extract channel ID from.
        
    Returns:
        Channel ID if found, None otherwise.
    """
    if not url or not url.strip():
        return None
    
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None
    
    # Check if it's a YouTube domain
    netloc = parsed.netloc.lower()
    if netloc not in ("youtube.com", "www.youtube.com"):
        return None
    
    # Extract path and remove leading/trailing slashes
    path = parsed.path.strip('/')
    
    # Check if path matches /channel/<ID> pattern
    match = re.match(r"^channel/([^/]+)(?:/.*)?$", path)
    if match:
        return match.group(1)
    
    return None