"""Kopier/indsæt kode til Jupyter for at filtrere store Reddit .zst dumps til r/denmark.

Brug:
1) Kør denne celle først (funktioner)
2) Kør eksemplerne nederst (RC/RS)
"""

import io
import json
from pathlib import Path

import pandas as pd
import zstandard as zstd


def filter_reddit_zst_to_subreddit(
    input_path,
    output_path,
    subreddit="denmark",
    columns=None,
    progress_every=1_000_000,
):
    """Streamer input .zst og skriver kun rows fra valgt subreddit til output .jsonl.zst.

    Parameters
    ----------
    input_path : str | Path
        Sti til fx RC_2025-08.zst eller RS_2025-08.zst.
    output_path : str | Path
        Sti til filtreret output, fx RC_2025-08_denmark.jsonl.zst.
    subreddit : str
        Subreddit der beholdes (case-insensitive).
    columns : list[str] | None
        Felter der beholdes i output. Hvis None bruges fornuftig default.
    progress_every : int
        Print status hver N linjer.
    """
    default_columns = [
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
    keep_columns = columns or default_columns

    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    subreddit = subreddit.lower().strip()
    total = kept = bad_json = 0

    dctx = zstd.ZstdDecompressor(max_window_size=2**31)
    cctx = zstd.ZstdCompressor(level=3, threads=-1)

    with input_path.open("rb") as ifh, output_path.open("wb") as ofh:
        with dctx.stream_reader(ifh) as reader, cctx.stream_writer(ofh) as writer:
            text_reader = io.TextIOWrapper(reader, encoding="utf-8")
            text_writer = io.TextIOWrapper(writer, encoding="utf-8")

            for line in text_reader:
                total += 1
                if progress_every and total % progress_every == 0:
                    print(f"Processed {total:,} rows | kept {kept:,}")

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    bad_json += 1
                    continue

                if str(row.get("subreddit", "")).lower() != subreddit:
                    continue

                kept += 1
                trimmed = {k: row.get(k) for k in keep_columns if k in row}
                text_writer.write(json.dumps(trimmed, ensure_ascii=False) + "\n")

            text_writer.flush()

    pct = (kept / total * 100) if total else 0
    print("Færdig")
    print(f"- Total rows: {total:,}")
    print(f"- Kept rows: {kept:,} ({pct:.4f}%)")
    print(f"- Bad JSON: {bad_json:,}")
    print(f"- Output: {output_path}")


# --- EKSEMPEL 1: filtrér comments ---
# filter_reddit_zst_to_subreddit(
#     input_path="/sti/til/RC_2025-08.zst",
#     output_path="/sti/til/RC_2025-08_denmark.jsonl.zst",
#     subreddit="denmark",
# )

# --- EKSEMPEL 2: filtrér submissions ---
# filter_reddit_zst_to_subreddit(
#     input_path="/sti/til/RS_2025-08.zst",
#     output_path="/sti/til/RS_2025-08_denmark.jsonl.zst",
#     subreddit="denmark",
# )


def load_jsonl_zst_sample(path, max_rows=200_000):
    """Læs et begrænset antal rows fra .jsonl.zst til pandas DataFrame."""
    rows = []
    with open(path, "rb") as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text = io.TextIOWrapper(reader, encoding="utf-8")
            for i, line in enumerate(text):
                rows.append(json.loads(line))
                if i + 1 >= max_rows:
                    break
    return pd.DataFrame(rows)


# --- EKSEMPEL 3: læs sample i notebook ---
# df = load_jsonl_zst_sample("/sti/til/RC_2025-08_denmark.jsonl.zst", max_rows=100_000)
# df.head()
