from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.logging_config import configure_logging  # noqa: E402


API_URL = "https://cs.wikipedia.org/w/api.php"
logger = logging.getLogger(__name__)
STOPWORDS = {
    "a",
    "aby",
    "ale",
    "byl",
    "byla",
    "bylo",
    "byly",
    "co",
    "jak",
    "jaká",
    "jaké",
    "jaký",
    "jakých",
    "je",
    "jsou",
    "kdo",
    "kdy",
    "lze",
    "na",
    "nebo",
    "po",
    "pro",
    "proč",
    "se",
    "tak",
    "v",
    "ve",
    "za",
    "že",
}
CURATED_TOPICS = [
    "České dějiny",
    "Dějiny Československa",
    "Československo",
    "Husitství",
    "Karel IV.",
    "Bitva na Bílé hoře",
    "České národní obrození",
    "Vznik Československa",
    "První republika",
    "Versailleská smlouva",
    "Druhá světová válka",
    "Mnichovská dohoda",
    "Protektorát Čechy a Morava",
    "Únor 1948",
    "Komunistický režim v Československu",
    "Politické procesy v Československu",
    "Kolektivizace v Československu",
    "Pražské jaro",
    "Normalizace v Československu",
    "Železná opona v Československu",
    "Paměť národa",
    "Ústav pro studium totalitních režimů",
    "Místa paměti",
    "Věra Sosnarová",
    "Katolická církev v Československu",
    "Pronásledování katolické církve v Československu",
    "Řeholní řády",
    "Sametová revoluce",
    "Den vítězství",
    "Historiografie",
    "Historický pramen",
    "Dějepis",
    "Muzejní pedagogika",
    "Rámcový vzdělávací program",
    "Kontrafaktuální historie",
    "Evropská unie",
    "Dějiny Evropské unie",
    "Čína",
    "Dějiny Číny",
    "Hnutí za občanská práva",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Czech Wikipedia pages for RAG testing.")
    parser.add_argument("--questions", default="questions.txt", help="Question seed file.")
    parser.add_argument("--output", default="data/raw/wikipedia", help="Output directory.")
    parser.add_argument("--limit", type=int, default=100, help="Approximate number of pages to save.")
    parser.add_argument("--search-per-question", type=int, default=5)
    args = parser.parse_args()

    configure_logging("download-wikipedia", console=False)
    questions = _read_questions(Path(args.questions))
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    _log(f"Reading questions from {args.questions}")
    if args.limit <= 0:
        _log("Limit is 0; nothing to download")
        return

    existing_files = {path.name for path in output_dir.glob("*.md")}
    if existing_files:
        _log(f"Found {len(existing_files)} existing Wikipedia files; they will be skipped")

    candidate_limit = args.limit + len(existing_files)
    titles = collect_titles(questions, candidate_limit, args.search_per_question)
    _log(f"Selected {len(titles)} candidate titles")
    saved = download_pages(titles, output_dir, target_new_files=args.limit)
    _log(f"Saved {saved} Wikipedia pages to {output_dir}")


def collect_titles(questions: list[str], limit: int, search_per_question: int) -> list[str]:
    titles: list[str] = []
    seen: set[str] = set()
    with httpx.Client(timeout=30.0, headers={"User-Agent": "czech-history-rag-mvp/0.1"}) as client:
        _log(f"Adding curated seed topics first ({len(CURATED_TOPICS)} topics)")
        for topic in CURATED_TOPICS:
            _add_title(titles, seen, topic)
            if len(titles) >= limit:
                return titles

        _log("Searching Czech Wikipedia from questions to fill the remaining slots")
        for query in _queries_from_questions(questions):
            for title in search_titles(client, query, search_per_question):
                _add_title(titles, seen, title)
                if len(titles) >= limit:
                    return titles
            time.sleep(0.1)
    return titles


def search_titles(client: httpx.Client, query: str, limit: int) -> list[str]:
    response = client.get(
        API_URL,
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
            "utf8": 1,
        },
    )
    response.raise_for_status()
    data = response.json()
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def download_pages(titles: list[str], output_dir: Path, target_new_files: int) -> int:
    if target_new_files <= 0:
        return 0

    saved = 0
    with httpx.Client(timeout=30.0, headers={"User-Agent": "czech-history-rag-mvp/0.1"}) as client:
        for index, title in enumerate(titles, start=1):
            expected_path = output_dir / f"{_slugify(title)}.md"
            if expected_path.exists():
                _log(f"[{index}/{len(titles)}] already present: {title} -> {expected_path}")
                continue

            page = fetch_page(client, title)
            if not page:
                _log(f"[{index}/{len(titles)}] skipped: {title}")
                continue
            path = output_dir / f"{_slugify(page['title'])}.md"
            if path.exists():
                _log(f"[{index}/{len(titles)}] already present: {page['title']} -> {path}")
                continue
            path.write_text(_format_page(page), encoding="utf-8")
            saved += 1
            _log(f"[{index}/{len(titles)}] downloaded: {page['title']} -> {path}")
            if saved >= target_new_files:
                break
            time.sleep(0.1)
    return saved


def fetch_page(client: httpx.Client, title: str) -> dict[str, str] | None:
    response = client.get(
        API_URL,
        params={
            "action": "query",
            "prop": "extracts|info",
            "titles": title,
            "explaintext": 1,
            "exsectionformat": "plain",
            "inprop": "url",
            "redirects": 1,
            "format": "json",
            "utf8": 1,
        },
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        text = (page.get("extract") or "").strip()
        if len(text.split()) < 80:
            return None
        return {
            "title": page.get("title") or title,
            "url": page.get("fullurl") or f"https://cs.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
            "text": text,
        }
    return None


def _format_page(page: dict[str, str]) -> str:
    return (
        "---\n"
        f"title: {page['title']}\n"
        f"url: {page['url']}\n"
        "source_name: Wikipedia\n"
        "document_type: encyclopedia\n"
        "---\n\n"
        f"# {page['title']}\n\n"
        f"{page['text']}\n"
    )


def _queries_from_questions(questions: list[str]) -> list[str]:
    queries: list[str] = []
    for question in questions:
        cleaned = re.sub(r"[^\wÁ-ž ]+", " ", question)
        words = [word for word in cleaned.split() if len(word) > 2 and word.lower() not in STOPWORDS]
        if words:
            queries.append(" ".join(words[:7]))
        queries.append(question)
    return queries


def _read_questions(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _add_title(titles: list[str], seen: set[str], title: str) -> None:
    normalized = title.strip()
    if normalized and normalized not in seen:
        titles.append(normalized)
        seen.add(normalized)


def _log(message: str) -> None:
    print(message)
    logger.info(message)


def _slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9áčďéěíňóřšťúůýž-]+", "", slug)
    return slug.strip("-") or "page"


if __name__ == "__main__":
    main()
