"""Command-line interface for tech tracker."""

import argparse
import json
import sys
from datetime import timezone
from typing import Any, Dict, List

from tech_tracker.app.youtube import fetch_youtube_videos_from_config
from tech_tracker.downloader import UrllibFeedDownloader
from tech_tracker.item_store import JsonItemStore
from tech_tracker.sources.youtube.to_items import youtube_videos_to_items


def serialize_videos_for_json(videos_by_url: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Serialize videos for JSON output.
    
    Converts datetime objects to ISO strings with 'Z' suffix for UTC.
    
    Args:
        videos_by_url: Dictionary mapping URLs to video lists.
        
    Returns:
        Serialized dictionary ready for JSON output.
    """
    result: Dict[str, List[Dict[str, Any]]] = {}
    
    for url, videos in videos_by_url.items():
        serialized_videos = []
        
        for video in videos:
            serialized_video = dict(video)  # Make a copy
            
            # Convert datetime to ISO string with 'Z' suffix
            if "published" in serialized_video and serialized_video["published"]:
                published = serialized_video["published"]
                if hasattr(published, "astimezone"):
                    # Ensure UTC and format with 'Z' suffix
                    utc_time = published.astimezone(timezone.utc)
                    serialized_video["published"] = utc_time.isoformat().replace("+00:00", "Z")
            
            serialized_videos.append(serialized_video)
        
        result[url] = serialized_videos
    
    return result


def handle_youtube_command(args: argparse.Namespace) -> int:
    """Handle the 'youtube' subcommand.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    if not args.config:
        print("Error: --config is required for youtube command", file=sys.stderr)
        return 1
    
    try:
        # Create downloader and fetch videos
        downloader = UrllibFeedDownloader()
        videos_by_url = fetch_youtube_videos_from_config(args.config, downloader)
        
        # If --store is provided, save items to store
        if args.store:
            # Convert videos to items
            items = youtube_videos_to_items(videos_by_url)
            
            # Save to store
            store = JsonItemStore(args.store)
            store.save_many(items)
        
        # Serialize for JSON output (still output videos, not items)
        output_data = serialize_videos_for_json(videos_by_url)
        
        # Output JSON to stdout
        json.dump(output_data, sys.stdout, indent=2)
        print()  # Add newline
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv if None).
        
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    parser = argparse.ArgumentParser(
        prog="tech-tracker",
        description="Tech tracking tool for RSS feeds and YouTube channels"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # YouTube subcommand
    youtube_parser = subparsers.add_parser(
        "youtube",
        help="Fetch videos from YouTube channels in config"
    )
    youtube_parser.add_argument(
        "--config",
        required=True,
        help="Path to TOML configuration file"
    )
    youtube_parser.add_argument(
        "--store",
        type=str,
        required=False,
        help="Path to item store JSON file. When provided, fetched YouTube videos are converted to items and saved."
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # Handle commands
    if args.command == "youtube":
        return handle_youtube_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())