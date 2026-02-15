# Notebook-klar løsning: Reddit `.zst` → kun `r/denmark`

Du bad om kode, du kan **kopiere direkte ind i Jupyter**. Brug filen her:

- `docs/reddit_denmark_notebook_klar_kode.py`

## Hurtig brug

1. Installer dependency i notebook/terminal:

```bash
pip install zstandard pandas
```

2. Åbn `docs/reddit_denmark_notebook_klar_kode.py`, kopiér hele indholdet ind i en notebook-celle, og kør cellen.

3. Kør derefter en af disse i en ny celle:

```python
filter_reddit_zst_to_subreddit(
    input_path="/sti/til/RC_2025-08.zst",
    output_path="/sti/til/RC_2025-08_denmark.jsonl.zst",
    subreddit="denmark",
)
```

```python
filter_reddit_zst_to_subreddit(
    input_path="/sti/til/RS_2025-08.zst",
    output_path="/sti/til/RS_2025-08_denmark.jsonl.zst",
    subreddit="denmark",
)
```

4. Læs et kontrolleret sample til analyse:

```python
df = load_jsonl_zst_sample("/sti/til/RC_2025-08_denmark.jsonl.zst", max_rows=100_000)
df.head()
```

## Hvorfor det virker

- Filerne streames linje for linje (ingen fuld indlæsning i RAM).
- Output holdes komprimeret (`.jsonl.zst`) og meget mindre.
- Notebook arbejder kun med den filtrerede data eller et sample.
