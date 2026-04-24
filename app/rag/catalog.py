from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.rag.chunking import Chunk


def save_chunk_catalog(path: Path, chunks: list[Chunk]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            payload = {"chunk_id": chunk.chunk_id, "text": chunk.text, "metadata": chunk.metadata}
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_chunk_catalog(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

