import argparse
import json
from pathlib import Path
from datetime import datetime, UTC


def main():
    parser = argparse.ArgumentParser(
        description="Convert yt-dlp videos.jsonl to target JSON format."
    )
    parser.add_argument(
        "input", type=Path, help="Input jsonl file (e.g., videos.jsonl)"
    )
    parser.add_argument("output", type=Path, help="Output json file (e.g., items.json)")
    args = parser.parse_args()
    items = []
    with args.input.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
            item = {
                "item_id": f"youtube:{obj['id']}",
                "source_type": "youtube",
                "source_url": obj["channel_url"],
                "title": obj["title"],
                "link": obj["original_url"],
                "published": datetime.fromtimestamp(obj["timestamp"], UTC)
                .isoformat()
                .replace("+00:00", "Z"),
                "seen": False,
            }
            items.append(item)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, indent=2)
    print(f"Written {len(items)} items to {args.output}")


if __name__ == "__main__":
    main()
