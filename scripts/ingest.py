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
    parser = argparse.ArgumentParser(description="Ingest local documents into the rag-avatar Qdrant collection.")
    parser.add_argument("--path", default=None, help="File or directory to ingest. Defaults to RAW_DATA_DIR.")
    parser.add_argument("--no-reset", action="store_true", help="Do not recreate the Qdrant collection.")
    args = parser.parse_args()

    configure_logging("ingest")
    settings = get_settings()
    path = Path(args.path) if args.path else settings.raw_data_dir
    result = RAGPipeline(settings).ingest(path, reset=not args.no_reset)
    print(f"Loaded documents: {result['documents_loaded']}")
    print(f"Indexed chunks: {result['chunks_indexed']}")
    print(f"Collection: {result['collection']}")


if __name__ == "__main__":
    main()
