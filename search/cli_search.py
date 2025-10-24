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
from search.utilities import Utilities

async def main():
    utils = Utilities()
    parser = argparse.ArgumentParser(description='ForArchives CLI Search')
    parser.add_argument('--query', default='', help='Search query')
    parser.add_argument('--archives', type=str, default='[0,1,2,3]', help='JSON array of archive indices')
    parser.add_argument('--board', default='_', help='Board to search in')
    parser.add_argument('--limit', type=int, default=100, help='Limit number of results')
    parser.add_argument('--subject', help='Search within threads with this subject')
    parser.add_argument('--delay', type=float, default=3.0, help='Delay between requests in seconds')
    parser.add_argument('--case-sensitive', action='store_true', help='Enable case-sensitive search')
    parser.add_argument('--format', choices=['json', 'text', 'stats'], default='json', help='Output format')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    archives = json.loads(args.archives)
    
    searcher = MoeSearcher()
    
    if args.subject:
        results = await searcher.searchInSubject(
            archives=archives,
            subject=args.subject,
            text=args.query,
            board=args.board,
            limit=args.limit,
            delay=args.delay,
            case=args.case_sensitive
        )
    else:
        results = await searcher.multiArchiveSearch(
            archives=archives,
            text=args.query,
            board=args.board,
            limit=args.limit,
            delay=args.delay
        )
    
    if args.format == 'json':
        output = json.dumps(results, indent=2)
    elif args.format == 'stats':
        stats = await searcher.calculate_statistics(results, args.query)
        output = json.dumps(stats, indent=2)
    else:
        output = searcher.formatText(results)
    
    if args.save:
        output_path = args.output or os.path.join(
            utils.log_dir,
            f"search_{utils.clean_filename(args.query)}.{args.format}"
        )
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Results saved to {output_path}")
    else:
        print(output)

if __name__ == '__main__':
    asyncio.run(main()) 
