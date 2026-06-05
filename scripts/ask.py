from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.rag.pipeline import RAGPipeline  # noqa: E402
from app.rag.placeholders import (  # noqa: E402
    DEFAULT_PLACEHOLDERS,
    load_placeholders,
    placeholder_defs_from_records,
)
from app.rag.prompts import (  # noqa: E402
    default_system_prompt_template,
    default_user_prompt_template,
    resolve_placeholder_defs,
    template_placeholder_names,
)


def _parse_selection(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"--selection must be name=value, got: {raw!r}")
    name, value = raw.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"--selection name must be non-empty, got: {raw!r}")
    return name, value


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask one question against the local RAG index.")
    parser.add_argument("question", help="Question to answer.")
    parser.add_argument(
        "--selection",
        action="append",
        default=[],
        type=_parse_selection,
        metavar="NAME=VALUE",
        help=(
            "Set a parameter placeholder, e.g. --selection length=short or "
            "--selection custom_instructions='Buď stručný.'. Repeatable."
        ),
    )
    parser.add_argument(
        "--length",
        default=None,
        help="Shortcut for --selection length=VALUE (e.g. short, medium, long).",
    )
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()

    configure_logging("ask")
    settings = get_settings()

    selections: dict[str, str] = dict(args.selection)
    if args.length is not None:
        selections["length"] = args.length

    # Resolve placeholder defs the same way the server does: shared overlay over
    # the DEFAULT_PLACEHOLDERS code floor, for the tokens the default prompts use.
    system_template = default_system_prompt_template()
    user_template = default_user_prompt_template()
    names = template_placeholder_names(system_template) | template_placeholder_names(user_template)
    shared_global = placeholder_defs_from_records(load_placeholders(settings.placeholders_path))
    placeholder_defs = resolve_placeholder_defs(
        names,
        shared_global_defs=shared_global,
        code_default_defs=DEFAULT_PLACEHOLDERS,
    )

    # Output-token budget keys on short/medium/long; mirror main.chat's derivation.
    length_def = placeholder_defs.get("length")
    length = selections.get("length") or (length_def.default if length_def else "medium") or "medium"

    response = RAGPipeline(settings).chat(
        question=args.question,
        length=length,
        placeholder_defs=placeholder_defs,
        selections=selections,
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
