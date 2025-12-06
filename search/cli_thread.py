#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add the server directory to Python path
server_dir = str(Path(__file__).parent.parent)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from search.moesearcher import MoeSearcher


async def main():
    parser = argparse.ArgumentParser(description="ForArchives Thread CLI")
    parser.add_argument("--thread", required=True, help="Thread ID")
    parser.add_argument("--archive", type=int, default=0, help="Archive index")
    parser.add_argument("--board", help="Board name")
    parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument("--save", action="store_true", help="Save to file")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    searcher = MoeSearcher()
    thread = await searcher.fetch_thread(
        archive=args.archive, board=args.board, thread_num=args.thread
    )

    if args.format == "json":
        output = json.dumps(thread, indent=2)
    else:
        output = searcher.formatText(thread)

    if args.save:
        output_path = args.output or f"thread_{args.thread}.{args.format}"
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Thread saved to {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    asyncio.run(main())
