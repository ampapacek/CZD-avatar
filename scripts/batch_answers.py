from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.logging_config import configure_logging  # noqa: E402
from app.rag.pipeline import RAGPipeline  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Answer all questions from a text file and save them to disk.")
    parser.add_argument("--questions", default="questions.txt", help="Path to the input questions file.")
    parser.add_argument("--output", default="answers_avatar.txt", help="Path to the output answers file.")
    parser.add_argument("--style", default="ucitel", help="Answer style to use.")
    parser.add_argument("--length", default="medium", help="Answer length to use.")
    args = parser.parse_args()

    configure_logging("batch-answers")
    settings = get_settings()
    pipeline = RAGPipeline(settings)

    questions_path = Path(args.questions)
    output_path = Path(args.output)
    questions = [line.strip() for line in questions_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    sections: list[str] = []
    try:
        for index, question in enumerate(questions, start=1):
            response = pipeline.chat(question=question, style=args.style, length=args.length)
            source_lines = [
                f"- [{source.citation_id}] {source.title or source.source_path}"
                + (f", str. {source.page_number}" if source.page_number else "")
                + (f", {source.url}" if source.url else "")
                for source in response.sources
            ]
            sections.append(
                "\n".join(
                    [
                        f"Q{index}: {question}",
                        f"A{index}: {response.answer}",
                        "Zdroje:",
                        *source_lines,
                        "",
                    ]
                ).strip()
            )
    finally:
        pipeline.close()

    output_path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote {len(questions)} answers to {output_path}")


if __name__ == "__main__":
    main()
