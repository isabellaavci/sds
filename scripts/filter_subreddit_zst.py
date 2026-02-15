#!/usr/bin/env python3
"""Stream-filter large Reddit .zst dumps to one subreddit without loading data into memory.

Example:
    python scripts/filter_subreddit_zst.py \
      --input /data/RC_2025-08.zst \
      --output /data/RC_2025-08_denmark.jsonl.zst \
      --subreddit denmark
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import zstandard as zstd


DEFAULT_COLUMNS = [
    "id",
    "created_utc",
    "subreddit",
    "author",
    "title",
    "selftext",
    "body",
    "score",
    "num_comments",
    "permalink",
    "link_id",
    "parent_id",
    "is_self",
    "over_18",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Filter newline-delimited JSON records in a .zst Reddit dump to one subreddit, "
            "while streaming to avoid high memory use."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to input .zst file")
    parser.add_argument("--output", required=True, type=Path, help="Path to output .jsonl.zst file")
    parser.add_argument(
        "--subreddit",
        default="denmark",
        help="Subreddit name to keep (case-insensitive). Default: denmark",
    )
    parser.add_argument(
        "--columns",
        nargs="*",
        default=DEFAULT_COLUMNS,
        help=(
            "Optional set of fields to keep in output. "
            "Default keeps useful fields for both submissions/comments."
        ),
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1_000_000,
        help="Print progress every N input rows. Default: 1,000,000",
    )
    return parser.parse_args()


def trim_record(record: dict, columns: list[str]) -> dict:
    return {key: record.get(key) for key in columns if key in record}


def stream_filter(
    input_path: Path,
    output_path: Path,
    subreddit: str,
    columns: list[str],
    progress_every: int,
) -> tuple[int, int, int]:
    subreddit = subreddit.lower().strip()
    total = 0
    kept = 0
    bad_json = 0

    dctx = zstd.ZstdDecompressor(max_window_size=2**31)
    cctx = zstd.ZstdCompressor(level=3, threads=-1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("rb") as ifh, output_path.open("wb") as ofh:
        with dctx.stream_reader(ifh) as reader, cctx.stream_writer(ofh) as writer:
            text_reader = io.TextIOWrapper(reader, encoding="utf-8")
            text_writer = io.TextIOWrapper(writer, encoding="utf-8")

            for line in text_reader:
                total += 1
                if progress_every and total % progress_every == 0:
                    print(f"Processed {total:,} rows, kept {kept:,}", file=sys.stderr)

                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    bad_json += 1
                    continue

                if str(obj.get("subreddit", "")).lower() != subreddit:
                    continue

                kept += 1
                trimmed = trim_record(obj, columns)
                text_writer.write(json.dumps(trimmed, ensure_ascii=False) + "\n")

            text_writer.flush()

    return total, kept, bad_json


def main() -> int:
    args = parse_args()

    if not args.input.exists():
        print(f"Input file not found: {args.input}", file=sys.stderr)
        return 2

    total, kept, bad_json = stream_filter(
        input_path=args.input,
        output_path=args.output,
        subreddit=args.subreddit,
        columns=args.columns,
        progress_every=args.progress_every,
    )

    pct = (kept / total * 100) if total else 0.0
    print(f"Done. Total rows: {total:,}")
    print(f"Kept rows: {kept:,} ({pct:.4f}%)")
    print(f"Bad JSON rows skipped: {bad_json:,}")
    print(f"Output written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
