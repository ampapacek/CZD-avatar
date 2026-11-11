"""Rewrite source links to their public form (instance config ``[[link_rewrites]]``).

Document URLs from the index and from mSearch can point at storage that needs a
login. When a public read-only link to the same files exists, a rewrite maps
the private URL prefix to the public one. The rest of the path is decoded and
re-encoded so it is safe both as a path and as a query value (e.g. a Seafile
share link ``.../files/?p=/<path>``), and the ``#page=N`` fragment is kept.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, unquote

from app.rag.wp_config import LinkRewrite, link_rewrites

URL_METADATA_KEYS = ("url", "document_url", "source_url")


def rewrite_url(url: str, rewrites: list[LinkRewrite]) -> str:
    """Return ``url`` with the first matching rewrite applied, else unchanged."""

    if not url:
        return url
    for rewrite in rewrites:
        if not url.startswith(rewrite.from_prefix):
            continue
        rest, hash_sign, fragment = url[len(rewrite.from_prefix) :].partition("#")
        return f"{rewrite.to_prefix}{quote(unquote(rest), safe='/')}{hash_sign}{fragment}"
    return url


def public_url(url: str) -> str:
    """Apply the active instance's link rewrites to ``url``."""

    return rewrite_url(url, link_rewrites())


def rewrite_chunk_links(chunks: list[dict[str, Any]], rewrites: list[LinkRewrite] | None = None) -> None:
    """Rewrite the URL fields of retrieved chunks' metadata in place."""

    active = link_rewrites() if rewrites is None else rewrites
    if not active:
        return
    for chunk in chunks:
        metadata = chunk.get("metadata")
        if not isinstance(metadata, dict):
            continue
        for key in URL_METADATA_KEYS:
            value = metadata.get(key)
            if isinstance(value, str):
                metadata[key] = rewrite_url(value, active)
