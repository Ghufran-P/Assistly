"""
Handles all communication with the Kaggle API:
- searching for datasets relevant to a user's question
- downloading dataset files locally (with a size guard)

Requires a Kaggle API token saved at ~/.kaggle/kaggle.json
(Account -> Settings -> API -> Create New Token on kaggle.com)
"""

import os
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

DATA_DIR = Path("data/kaggle_downloads")
MAX_DATASET_SIZE_MB = 100  # safety cap so we don't fill up disk / choke the local embedder

_api = None


def get_api():
    """Lazily authenticate and cache the Kaggle API client."""
    global _api
    if _api is None:
        _api = KaggleApi()
        _api.authenticate()  # reads ~/.kaggle/kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY env vars
    return _api


def search_datasets(query: str, max_results: int = 5):
    """Search Kaggle for datasets matching the query, sorted by relevance."""
    api = get_api()
    datasets = api.dataset_list(search=query, sort_by="votes")
    results = []
    for d in datasets[:max_results]:
        results.append(
            {
                "ref": d.ref,  # e.g. "owner/dataset-slug"
                "title": getattr(d, "title", d.ref),
                "size": getattr(d, "size", "unknown"),
                "url": f"https://www.kaggle.com/datasets/{d.ref}",
            }
        )
    return results


def download_dataset(ref: str, max_size_mb: int = MAX_DATASET_SIZE_MB) -> Path:
    """
    Download + unzip a dataset by its ref ("owner/slug") into
    data/kaggle_downloads/<owner__slug>/. Returns the folder path.

    If the dataset already looks downloaded (folder exists & non-empty), skip re-downloading.
    """
    api = get_api()
    dest = DATA_DIR / ref.replace("/", "__")

    if dest.exists() and any(dest.rglob("*")):
        return dest

    dest.mkdir(parents=True, exist_ok=True)
    api.dataset_download_files(ref, path=str(dest), unzip=True, quiet=True)

    # Size guard: if it somehow ballooned past the cap, trim the largest files first
    files = [f for f in dest.rglob("*") if f.is_file()]
    total_bytes = sum(f.stat().st_size for f in files)
    max_bytes = max_size_mb * 1024 * 1024
    if total_bytes > max_bytes:
        files.sort(key=lambda f: f.stat().st_size, reverse=True)
        for f in files:
            if total_bytes <= max_bytes:
                break
            total_bytes -= f.stat().st_size
            f.unlink()

    return dest
