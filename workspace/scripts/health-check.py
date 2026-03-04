#!/usr/bin/env python3
"""
Health Check - Scan Discord channels and create missing folder structures.

Usage:
  python3 health-check.py [--fix] [--notify]

Options:
  --fix     Create missing folders/files
  --notify  Print Discord notification summary
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

# Config
WORKSPACE = Path("/root/.openclaw/workspace")
DISCORD_DIR = WORKSPACE / "discord"
OPS_LOG = WORKSPACE / "system" / "ops.log"

# Known channels (name -> id mapping)
KNOWN_CHANNELS = {
    "bytebles": "1478055780409278464",
    "knights-of-st-joseph": "1478055869496430622",
    "santa-casa": "1477916233524580403",
    "acutis-flow": "1477911414646636614",
}

REQUIRED_STRUCTURE = [
    "purpose.md",
    "activity.log",
    "agent/manual.md",
    "sources/.gitkeep",
    "user/.gitkeep",
]


def log_to_ops(message: str):
    """Append timestamped entry to ops.log"""
    timestamp = datetime.now(timezone.utc).strftime("%a %Y-%m-%d %H:%M UTC")
    entry = f"[{timestamp}] {message}\n"
    with open(OPS_LOG, "a") as f:
        f.write(entry)


def check_channel(channel_name: str, fix: bool) -> dict:
    """Check a channel folder and optionally fix missing items."""
    channel_dir = DISCORD_DIR / channel_name
    result = {
        "name": channel_name,
        "missing": [],
        "created": [],
        "ok": True,
    }

    # Create folder if missing
    if not channel_dir.exists():
        result["missing"].append("folder")
        if fix:
            channel_dir.mkdir(parents=True, exist_ok=True)
            result["created"].append("folder")

    # Check required structure
    for item in REQUIRED_STRUCTURE:
        item_path = channel_dir / item
        if not item_path.exists():
            result["missing"].append(item)
            result["ok"] = False
            if fix:
                item_path.parent.mkdir(parents=True, exist_ok=True)
                item_path.touch()

                # Add default content for purpose.md if new
                if item == "purpose.md":
                    item_path.write_text(f"# #{channel_name}\n\nChannel purpose not yet defined.\n")

                result["created"].append(item)

    return result


def main():
    parser = argparse.ArgumentParser(description="Health check for Discord channel folders")
    parser.add_argument("--fix", action="store_true", help="Create missing folders/files")
    parser.add_argument("--notify", action="store_true", help="Print Discord notification")
    args = parser.parse_args()

    if not DISCORD_DIR.exists():
        DISCORD_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    total_created = 0

    # Check all known channels
    for channel_name in KNOWN_CHANNELS:
        result = check_channel(channel_name, args.fix)
        results.append(result)
        total_created += len(result["created"])

    # Also scan for any existing folders that might need structure
    for item in DISCORD_DIR.iterdir():
        if item.is_dir() and item.name not in KNOWN_CHANNELS and item.name != "tasks.example.md":
            result = check_channel(item.name, args.fix)
            results.append(result)
            total_created += len(result["created"])

    # Build summary
    lines = ["**Health Check Complete**"]
    for r in results:
        if r["created"]:
            lines.append(f"• **{r['name']}**: Created {', '.join(r['created'])}")
        elif r["ok"]:
            lines.append(f"• **{r['name']}**: ✓ OK")
        elif r["missing"]:
            lines.append(f"• **{r['name']}**: Missing {', '.join(r['missing'])}")

    summary = "\n".join(lines)

    # Log to ops.log
    if args.fix and total_created > 0:
        log_to_ops(f"Health check: Created {total_created} items across {len(results)} channels")
    else:
        log_to_ops(f"Health check: Scanned {len(results)} channels, {total_created} items needed")

    print(summary)

    if args.notify:
        print(f"\n--- Discord Notification ---\n{summary}\n----------------------------\n")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
