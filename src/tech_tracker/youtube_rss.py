"""YouTube RSS feed parser module."""

from datetime import datetime, timezone
from typing import Any, Dict, List

import xml.etree.ElementTree as ET


def parse_youtube_feed(xml: str) -> List[Dict[str, Any]]:
    """Parse YouTube RSS (Atom) feed and extract video entries.
    
    Args:
        xml: XML string content of the YouTube RSS feed.
        
    Returns:
        List of video entries, each containing:
        - video_id: str (YouTube video ID)
        - title: str (Video title)
        - link: str (Video URL)
        - published: datetime (timezone-aware, UTC)
        
    Raises:
        ValueError: If XML parsing fails or feed format is invalid.
    """
    if not xml or not xml.strip():
        return []
    
    try:
        # Parse XML with namespace handling
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML: {e}") from e
    
    # Define namespace mappings for YouTube feeds
    namespaces = {
        "atom": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    
    # Find all entry elements
    entries = root.findall("atom:entry", namespaces)
    
    if not entries:
        return []
    
    videos = []
    
    for entry in entries:
        try:
            # Extract video ID
            video_id_elem = entry.find("yt:videoId", namespaces)
            if video_id_elem is None or video_id_elem.text is None:
                continue
            video_id = video_id_elem.text
            
            # Extract title
            title_elem = entry.find("atom:title", namespaces)
            if title_elem is None or title_elem.text is None:
                continue
            title = title_elem.text
            
            # Extract link (prefer alternate link)
            link = None
            for link_elem in entry.findall("atom:link", namespaces):
                rel = link_elem.get("rel", "")
                href = link_elem.get("href", "")
                if rel == "alternate" and href:
                    link = href
                    break
                elif not link and href:  # Fallback to any link with href
                    link = href
            
            if not link:
                continue
            
            # Extract and parse published date
            published_elem = entry.find("atom:published", namespaces)
            if published_elem is None or published_elem.text is None:
                continue
            
            published_str = published_elem.text
            # Handle ISO 8601 format with 'Z' suffix
            if published_str.endswith('Z'):
                published_str = published_str[:-1] + '+00:00'
            
            try:
                published = datetime.fromisoformat(published_str)
                # Ensure timezone-aware and in UTC
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
                else:
                    published = published.astimezone(timezone.utc)
            except ValueError as e:
                continue  # Skip entry with invalid date
            
            videos.append({
                "video_id": video_id,
                "title": title,
                "link": link,
                "published": published,
            })
            
        except Exception:
            # Skip malformed entries but continue processing others
            continue
    
    return videos