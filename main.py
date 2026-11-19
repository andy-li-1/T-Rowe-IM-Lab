"""CLI entry point.

Usage:
    python main.py data/transcripts/sample_call.txt
    python main.py data/transcripts/*.txt --out output
"""

import argparse
import sys

from tax_extractor import run, write_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract structured tax input from call transcripts.")
    parser.add_argument("transcripts", nargs="+", help="Transcript file(s)")
    parser.add_argument("--out", default="output", help="Output directory for JSON results")
    args = parser.parse_args()

    for path in args.transcripts:
        result = run(path)
        out_path = write_result(result, args.out)
        print(f"{path} -> {out_path}")
        for w in result.warnings:
            print(f"  ! {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
