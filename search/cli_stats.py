#!/usr/bin/env python3
import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add the server directory to Python path
server_dir = str(Path(__file__).parent.parent)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from search.moesearcher import MoeSearcher


async def main():
    parser = argparse.ArgumentParser(description="ForArchives Statistics CLI")
    parser.add_argument(
        "--archives",
        type=str,
        default="[0,1,2,3]",
        help="JSON array of archive indices",
    )
    parser.add_argument("--board", help="Board to analyze")
    parser.add_argument("--date", help="Date range (YYYY-MM-DD:YYYY-MM-DD)")
    parser.add_argument(
        "--format",
        choices=["json", "text", "csv"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()
    archives = json.loads(args.archives)

    searcher = MoeSearcher()
    date_range = None
    if args.date:
        start, end = args.date.split(":")
        date_range = (
            datetime.strptime(start, "%Y-%m-%d"),
            datetime.strptime(end, "%Y-%m-%d"),
        )

    results = await searcher.calculate_statistics(
        archives=archives, board=args.board, date_range=date_range
    )

    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif args.format == "csv":
        print("archive,total_posts,active_threads,avg_posts_per_thread")
        for archive, stats in results.items():
            print(
                f"{archive},{stats['total_posts']},{stats['active_threads']},{stats['avg_posts_per_thread']:.2f}"
            )
    else:
        for archive, stats in results.items():
            print(f"\nArchive: {archive}")
            print(f"Total Posts: {stats['total_posts']}")
            print(f"Active Threads: {stats['active_threads']}")
            print(f"Average Posts per Thread: {stats['avg_posts_per_thread']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
