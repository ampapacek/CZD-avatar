from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}
WP1_ROOT_MARKER = "WP1-2026-02-subset"
WP1_STORAGE_BASE = "https://storage.ufal.mff.cuni.cz/lib/2e093cea-cdcd-401d-a664-d1ca05112e55/file/v2026-02"


@dataclass(slots=True)
class Document:
    text: str
    metadata: dict[str, Any]


def load_documents(path: Path) -> list[Document]:
    """Load all supported files under a directory or a single supported file."""

    if not path.exists():
        raise FileNotFoundError(f"Document path does not exist: {path}")

    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    documents: list[Document] = []
    for file_path in files:
        suffix = file_path.suffix.lower()
        if suffix in {".txt", ".md"}:
            documents.append(_load_text_document(file_path))
        elif suffix == ".pdf":
            documents.extend(_load_pdf_document(file_path))
    return documents


def _load_text_document(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    frontmatter, body = _parse_frontmatter(raw)
    title = frontmatter.get("title") or _first_markdown_heading(body) or path.stem
    metadata = _build_base_metadata(
        path,
        {
            "title": title,
            "page_number": None,
            "historical_period": frontmatter.get("historical_period"),
            "document_type": frontmatter.get("document_type"),
            "url": frontmatter.get("url"),
            "source_name": frontmatter.get("source_name"),
        },
    )
    return Document(text=body, metadata=metadata)


def _load_pdf_document(path: Path) -> list[Document]:
    reader = PdfReader(str(path))
    title = None
    if reader.metadata and reader.metadata.title:
        title = str(reader.metadata.title)

    folder_metadata = _load_folder_metadata(path.parent)
    documents: list[Document] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue
        base_metadata = _build_base_metadata(
            path,
            {
                "title": folder_metadata.get("collection_title") or title or path.stem,
                "page_number": page_index,
                "historical_period": folder_metadata.get("historical_period"),
                "document_type": folder_metadata.get("document_type") or "pdf",
                "url": folder_metadata.get("url"),
                "source_name": folder_metadata.get("source_name"),
                "collection_id": folder_metadata.get("collection_id"),
                "collection_title": folder_metadata.get("collection_title"),
                "source_citation": folder_metadata.get("source_citation"),
                "source_license": folder_metadata.get("source_license"),
                "downloaded_at": folder_metadata.get("downloaded_at"),
            },
        )
        documents.append(Document(text=text, metadata=base_metadata))
    return documents


def _build_base_metadata(path: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    folder_metadata = _load_folder_metadata(path.parent)
    document_url = _build_wp1_storage_url(path)
    source_url = metadata.get("url") or folder_metadata.get("url")
    source_name = metadata.get("source_name") or folder_metadata.get("source_name")
    title = metadata.get("title") or folder_metadata.get("collection_title") or path.stem

    return {
        "source_path": str(path),
        "source_path_display": _display_source_path(path),
        "title": title,
        "page_number": metadata.get("page_number"),
        "historical_period": metadata.get("historical_period") or folder_metadata.get("historical_period"),
        "document_type": metadata.get("document_type") or folder_metadata.get("document_type"),
        "url": document_url or source_url,
        "document_url": document_url,
        "source_url": source_url,
        "source_name": (source_name or "Wikipedia") if "wikipedia" in str(path).lower() else source_name,
        "collection_id": metadata.get("collection_id") or folder_metadata.get("collection_id"),
        "collection_title": metadata.get("collection_title") or folder_metadata.get("collection_title"),
        "source_citation": metadata.get("source_citation") or folder_metadata.get("source_citation"),
        "source_license": metadata.get("source_license") or folder_metadata.get("source_license"),
        "downloaded_at": metadata.get("downloaded_at") or folder_metadata.get("downloaded_at"),
    }


def _load_folder_metadata(folder: Path) -> dict[str, str]:
    meta_path = folder / "meta.md"
    if not meta_path.exists():
        return {}

    raw = meta_path.read_text(encoding="utf-8", errors="ignore")
    metadata: dict[str, str] = {}
    for line in raw.splitlines():
        match = re.match(r"^\*\s+\*\*(.+?)\*\*:\s*(.*)$", line.strip())
        if not match:
            continue
        key = match.group(1).strip().lower()
        value = match.group(2).strip()
        metadata[_normalize_meta_key(key)] = value
    if metadata.get("zdroj_odkaz"):
        metadata["url"] = metadata["zdroj_odkaz"]
    if metadata.get("nazev"):
        metadata["collection_title"] = metadata["nazev"]
    if metadata.get("id"):
        metadata["collection_id"] = metadata["id"]
    if metadata.get("typ"):
        metadata["document_type"] = metadata["typ"]
    if metadata.get("citace"):
        metadata["source_citation"] = metadata["citace"]
    if metadata.get("licence"):
        metadata["source_license"] = metadata["licence"]
    if metadata.get("stazeno_dne"):
        metadata["downloaded_at"] = metadata["stazeno_dne"]
    return metadata


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse a tiny YAML-like frontmatter block without requiring PyYAML."""

    if not text.startswith("---"):
        return {}, text

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.DOTALL)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, match.group(2)


def _first_markdown_heading(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return None


def _build_wp1_storage_url(path: Path) -> str | None:
    parts = list(path.parts)
    if WP1_ROOT_MARKER not in parts:
        return None
    start = parts.index(WP1_ROOT_MARKER) + 1
    relative_parts = parts[start:]
    if not relative_parts:
        return None
    encoded = "/".join(quote(part, safe="") for part in relative_parts)
    return f"{WP1_STORAGE_BASE}/{encoded}"


def _display_source_path(path: Path) -> str:
    path_str = str(path)
    marker = "data/raw/"
    if marker in path_str:
        return path_str.split(marker, 1)[1]
    return path_str


def _normalize_meta_key(key: str) -> str:
    replacements = {
        "č": "c",
        "ř": "r",
        "š": "s",
        "ť": "t",
        "ž": "z",
        "ý": "y",
        "á": "a",
        "í": "i",
        "é": "e",
        "ó": "o",
        "ú": "u",
        "ů": "u",
        "ď": "d",
        "ň": "n",
    }
    normalized = key.lower()
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
    return normalized
