from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.rag.pipeline import RAGPipeline  # noqa: E402
from app.rag.prompts import available_lengths, available_styles  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask one question against the local RAG index.")
    parser.add_argument("question", help="Question to answer.")
    parser.add_argument("--style", default=None, choices=available_styles())
    parser.add_argument("--length", default=None, choices=available_lengths())
    parser.add_argument("--custom-instructions", default=None)
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()

    configure_logging("ask")
    settings = get_settings()
    style = args.style or settings.default_style
    length = args.length or settings.default_length
    response = RAGPipeline(settings).chat(
        question=args.question,
        style=style,
        length=length,
        custom_instructions=args.custom_instructions,
        top_k=args.top_k,
    )
    print(response.answer)
    print("\nZdroje:")
    for source in response.sources:
        page = f", str. {source.page_number}" if source.page_number else ""
        url = f", {source.url}" if source.url else ""
        print(f"- [{source.citation_id}] {source.title or source.source_path}{page}{url}")


if __name__ == "__main__":
    main()
