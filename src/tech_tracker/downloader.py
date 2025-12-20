"""Feed downloader interface and implementations."""

from typing import Protocol

import urllib.request


class FeedDownloader(Protocol):
    """Protocol for feed downloaders."""
    
    def fetch_text(self, url: str) -> str:
        """Fetch text content from a URL.
        
        Args:
            url: The URL to fetch from.
            
        Returns:
            The text content fetched from the URL.
            
        Raises:
            ValueError: If the URL is invalid or fetch fails.
        """
        ...


class UrllibFeedDownloader:
    """Feed downloader implementation using urllib."""
    
    def __init__(self, timeout: int = 10) -> None:
        """Initialize the downloader with a timeout.
        
        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
    
    def fetch_text(self, url: str) -> str:
        """Fetch text content from a URL using urllib.
        
        Args:
            url: The URL to fetch from.
            
        Returns:
            The text content fetched from the URL.
            
        Raises:
            ValueError: If the URL is invalid or fetch fails.
        """
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                # Check if response is successful
                if response.status != 200:
                    raise ValueError(f"HTTP error: {response.status}")
                
                # Read and decode response
                content = response.read()
                return content.decode('utf-8')
                
        except urllib.error.URLError as e:
            raise ValueError(f"Failed to fetch URL {url}: {e}") from e
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode response from {url}: {e}") from e