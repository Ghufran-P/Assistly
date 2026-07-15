"""
Turns raw dataset files (csv, tsv, json, txt, md) into small text chunks
("documents") that can be embedded and stored in the vector database.

Tabular files get two kinds of chunks:
  1. a "schema" chunk describing the columns (so the model can answer
     questions about structure, e.g. "what columns does this dataset have")
  2. row-group chunks (~20 rows each) so the model can answer questions
     about actual data values
"""

from pathlib import Path

import pandas as pd

TABULAR_EXT = {".csv", ".tsv"}
TEXT_EXT = {".txt", ".md", ".json"}

MAX_ROWS_SAMPLED = 500  # don't load huge files fully; sample is enough for RAG context
ROWS_PER_CHUNK = 20
TEXT_CHUNK_SIZE = 1500
TEXT_CHUNK_OVERLAP = 200


def load_folder_as_documents(folder: Path, dataset_ref: str):
    docs = []
    for file in sorted(folder.rglob("*")):
        if not file.is_file():
            continue
        suffix = file.suffix.lower()
        try:
            if suffix in TABULAR_EXT:
                docs.extend(_load_tabular(file, dataset_ref))
            elif suffix in TEXT_EXT:
                docs.extend(_load_text(file, dataset_ref))
        except Exception as e:
            print(f"[document_loader] Skipping {file.name}: {e}")
    return docs


def _load_tabular(file: Path, dataset_ref: str):
    sep = "\t" if file.suffix.lower() == ".tsv" else None
    df = pd.read_csv(
        file, nrows=MAX_ROWS_SAMPLED, sep=sep, engine="python", on_bad_lines="skip"
    )

    schema_text = (
        f"File '{file.name}' from Kaggle dataset '{dataset_ref}' has "
        f"{len(df.columns)} columns: {', '.join(str(c) for c in df.columns)}. "
        f"(showing a sample of up to {MAX_ROWS_SAMPLED} rows)"
    )
    docs = [{"text": schema_text, "source": f"{dataset_ref}/{file.name}", "type": "schema"}]

    for i in range(0, len(df), ROWS_PER_CHUNK):
        chunk = df.iloc[i : i + ROWS_PER_CHUNK]
        text = (
            f"Rows {i}-{i + len(chunk) - 1} from '{file.name}' ({dataset_ref}):\n"
            + chunk.to_string(index=False)
        )
        docs.append({"text": text, "source": f"{dataset_ref}/{file.name}", "type": "rows"})

    return docs


def _load_text(file: Path, dataset_ref: str):
    text = file.read_text(errors="ignore")
    docs = []
    start = 0
    while start < len(text):
        end = start + TEXT_CHUNK_SIZE
        docs.append(
            {
                "text": text[start:end],
                "source": f"{dataset_ref}/{file.name}",
                "type": "text",
            }
        )
        start = end - TEXT_CHUNK_OVERLAP
    return docs
