"""Command-line interface for tech tracker."""

import argparse
import json
import sys
from datetime import timezone
from typing import Any, Dict, List

from tech_tracker.app.youtube import fetch_youtube_videos_from_config
from tech_tracker.app.update import fetch_youtube_new_items
from tech_tracker.downloader import UrllibFeedDownloader
from tech_tracker.item_store import JsonItemStore
from tech_tracker.sources.youtube.to_items import youtube_videos_to_items


def default_store_path() -> "Path":
    """Get the default store path.
    
    Returns:
        Path to the default store file in user's home directory.
    """
    from pathlib import Path
    return Path.home() / ".tech-tracker" / "items.json"


def default_config_path() -> "Path":
    """Get the default config path.
    
    Returns:
        Path to the default config file in user's config directory.
    """
    from pathlib import Path
    return Path.home() / ".config" / "tech-tracker" / "config.toml"


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


def serialize_items_for_json(items: List["Item"]) -> Dict[str, List[Dict[str, Any]]]:
    """Serialize items for JSON output, grouped by source URL.
    
    Args:
        items: List of Item objects to serialize.
        
    Returns:
        Serialized dictionary ready for JSON output, grouped by source_url.
        If no items exist for a source URL, the URL will still be included with an empty list.
    """
    from tech_tracker.item import Item
    
    # Group items by source URL
    items_by_url: Dict[str, List[Item]] = {}
    for item in items:
        if item.source_url not in items_by_url:
            items_by_url[item.source_url] = []
        items_by_url[item.source_url].append(item)
    
    # Convert to JSON-serializable format
    result: Dict[str, List[Dict[str, Any]]] = {}
    for url, url_items in items_by_url.items():
        serialized_items = []
        for item in url_items:
            serialized_items.append(item.to_dict())
        result[url] = serialized_items
    
    return result


def handle_fetch_command(args: argparse.Namespace) -> int:
    """Handle the 'fetch' subcommand.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    # Determine config path (default if not provided)
    config_path = args.config if args.config is not None else default_config_path()
    
    # Create empty config file if it doesn't exist (only for default path)
    if args.config is None and not config_path.exists():
        from pathlib import Path
        # Create parent directory
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Create empty config file
        config_path.write_text("", encoding="utf-8")
        # Output user-friendly message
        print(f"Created default config: {config_path}")
    
    try:
        # Create downloader and fetch videos
        downloader = UrllibFeedDownloader()
        
        # Always use store mode: default path if --store not provided, specified path otherwise
        if args.store is None:
            store_path = default_store_path()
        else:
            store_path = args.store
        
        # Use fetch_youtube_new_items to get only new items (internal implementation)
        store = JsonItemStore(store_path)
        new_items = fetch_youtube_new_items(config_path, downloader, store)
        
        # Output only the new items
        output_data = serialize_items_for_json(new_items)
        
        # Output JSON to stdout
        json.dump(output_data, sys.stdout, indent=2)
        print()  # Add newline
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_recommend_command(args: argparse.Namespace) -> int:
    """Handle the 'recommend' subcommand.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    try:
        # Import required modules
        from tech_tracker.app.recommend import (
            LatestRecommender, 
            KeywordFromSeenRecommender,
            recommend_from_store, 
            render_recommendation_markdown,
            render_multi_recommendation_markdown
        )
        from tech_tracker.item_store import JsonItemStore
        from pathlib import Path
        
        # Use default store path
        store_path = default_store_path()
        store = JsonItemStore(store_path)
        
        # Generate recommendations from both recommenders
        latest_recommender = LatestRecommender()
        keyword_recommender = KeywordFromSeenRecommender()
        
        latest_result = recommend_from_store(store, latest_recommender)
        keyword_result = recommend_from_store(store, keyword_recommender)
        
        # Render multi-section markdown
        sections = [
            ("Latest", latest_result),
            ("Keyword from Seen", keyword_result)
        ]
        markdown_content = render_multi_recommendation_markdown(sections)
        
        # Write to current working directory
        output_file = Path.cwd() / "recommend.md"
        output_file.write_text(markdown_content, encoding="utf-8")
        
        # Output brief message to stdout
        print(f"Written to {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_modify_command(args: argparse.Namespace) -> int:
    """Handle the 'modify' subcommand.
    
    Args:
        args: Parsed command-line arguments.
        
    Returns:
        Exit code (0 for success, non-zero for error).
    """
    try:
        # Import required modules
        from tech_tracker.item import Item
        from tech_tracker.item_store import JsonItemStore
        from pathlib import Path
        
        # Check if action is provided (help was requested)
        if args.action is None:
            return 1
        
        # Determine store path (default if not provided)
        if args.store is None:
            store_path = default_store_path()
        else:
            store_path = args.store
        
        # Load items from store
        store = JsonItemStore(store_path)
        items = store.load_all()
        
        # Find the target item by ID
        target_item = None
        for item in items:
            if item.item_id == args.item_id:
                target_item = item
                break
        
        # If item not found, return error
        if target_item is None:
            print(f"Error: Item with ID '{args.item_id}' not found", file=sys.stderr)
            return 1
        
        # Create updated item with new seen status
        updated_item = Item(
            item_id=target_item.item_id,
            source_type=target_item.source_type,
            source_url=target_item.source_url,
            title=target_item.title,
            link=target_item.link,
            published=target_item.published,
            seen=args.action == "seen"  # True for seen, False for unseen
        )
        
        # Save the updated item (this will overwrite the existing one)
        store.save_many([updated_item])
        
        # Output success message
        action_word = "seen" if args.action == "seen" else "unseen"
        print(f"Marked item {args.item_id} as {action_word}")
        
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
        description="Tech tracking tool for RSS feeds and other sources"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Fetch subcommand
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch items from configured sources"
    )
    fetch_parser.add_argument(
        "--config",
        required=False,
        help="Path to TOML configuration file (default: ~/.config/tech-tracker/config.toml)"
    )
    fetch_parser.add_argument(
        "--store",
        type=str,
        required=False,
        help="Path to item store JSON file. When provided, fetched items are saved."
    )
    
    # Recommend subcommand
    recommend_parser = subparsers.add_parser(
        "recommend",
        help="Generate recommendations from stored items and save as Markdown"
    )
    
    # Modify subcommand
    modify_parser = subparsers.add_parser(
        "modify",
        help="Modify item properties (seen/unseen status)"
    )
    modify_parser.add_argument(
        "--store",
        type=str,
        required=False,
        help="Path to item store JSON file (default: ~/.tech-tracker/items.json)"
    )
    modify_subparsers = modify_parser.add_subparsers(dest="action", help="Modify actions")
    
    # Modify seen subcommand
    seen_parser = modify_subparsers.add_parser(
        "seen",
        help="Mark an item as seen"
    )
    seen_parser.add_argument(
        "item_id",
        help="ID of the item to mark as seen"
    )
    
    # Modify unseen subcommand
    unseen_parser = modify_subparsers.add_parser(
        "unseen",
        help="Mark an item as unseen"
    )
    unseen_parser.add_argument(
        "item_id",
        help="ID of the item to mark as unseen"
    )
    
    # Parse arguments
    args = parser.parse_args(argv)
    
    # Handle commands
    if args.command == "fetch":
        return handle_fetch_command(args)
    elif args.command == "recommend":
        return handle_recommend_command(args)
    elif args.command == "modify":
        return handle_modify_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())