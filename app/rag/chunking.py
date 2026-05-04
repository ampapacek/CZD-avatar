from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.rag.documents import Document


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_documents(documents: list[Document], chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc_index, document in enumerate(documents):
        text = clean_text(document.text)
        if not text:
            continue
        for local_index, chunk_text in enumerate(_paragraph_chunks(text, chunk_size, chunk_overlap)):
            metadata = dict(document.metadata)
            metadata["chunk_index"] = local_index
            metadata["word_count"] = len(chunk_text.split())
            base = metadata.get("source_path_display") or metadata.get("source_path") or metadata.get("title") or f"document-{doc_index}"
            page = metadata.get("page_number")
            page_part = f"-p{page}" if page else ""
            chunk_id = f"{base}{page_part}-chunk-{local_index}"
            chunks.append(Chunk(chunk_id=chunk_id, text=chunk_text, metadata=metadata))
    return chunks


def _paragraph_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current_parts: list[str] = []
    current_words = 0

    for paragraph in paragraphs:
        paragraph_words = paragraph.split()
        if len(paragraph_words) > chunk_size:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_words = 0
            chunks.extend(_word_window_chunks(paragraph_words, chunk_size, chunk_overlap))
            continue

        if current_words and current_words + len(paragraph_words) > chunk_size:
            chunks.append("\n\n".join(current_parts))
            overlap_text = _overlap_from_text(chunks[-1], chunk_overlap)
            current_parts = [overlap_text] if overlap_text else []
            current_words = len(overlap_text.split()) if overlap_text else 0

        current_parts.append(paragraph)
        current_words += len(paragraph_words)

    if current_parts:
        chunks.append("\n\n".join(current_parts))
    return chunks


def _word_window_chunks(words: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    step = max(chunk_size - chunk_overlap, 1)
    for start in range(0, len(words), step):
        window = words[start : start + chunk_size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + chunk_size >= len(words):
            break
    return chunks


def _overlap_from_text(text: str, overlap_words: int) -> str:
    if overlap_words <= 0:
        return ""
    words = text.split()
    return " ".join(words[-overlap_words:])
