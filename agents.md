# Agent Notes

This file is a practical handoff for future agents working in this repo.

## What this project is

- Czech-history RAG prototype with FastAPI backend and simple static frontend.
- Main goal: retrieve passages from local documents and answer in Czech with grounded citations.
- Current stack:
  - FastAPI
  - local/remote Qdrant
  - sentence-transformers embeddings
  - hybrid retrieval: dense + BM25
  - OpenRouter via OpenAI-compatible API for generation

## Important directories

- `app/main.py` - FastAPI app, routes, model presets, public settings, lifespan shutdown
- `app/models.py` - API request/response models
- `app/config.py` - settings loading
- `app/logging_config.py` - timestamped logging into `logs/`
- `app/rag/` - ingestion, chunking, retrieval, prompting, vector store, pipeline
- `app/static/` - frontend HTML/CSS/JS
- `scripts/ingest.py` - CLI ingestion
- `scripts/ask.py` - CLI ask
- `scripts/download_wikipedia.py` - test-data downloader
- `data/raw/` - source documents
- `data/processed/chunks.jsonl` - persisted chunk catalog for BM25/debug
- `data/qdrant/` - local Qdrant storage

## How to run

Use Python 3.12.

```bash
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

Ingest everything under `data/raw`:

```bash
python scripts/ingest.py --path data/raw
```

Run the app:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Quick CLI test:

```bash
python scripts/ask.py "Jaký byl význam husitských válek?"
```

## Config and a past gotcha

- `.env` is intentionally preferred over already-exported shell env vars.
- This was changed because an old exported `OPENROUTER_API_KEY` kept overriding the local `.env` key.
- If OpenRouter behaves strangely, check startup logs for the key fingerprint logged by `app/main.py`.
- Never print the actual key.

## Retrieval behavior

- Hybrid retrieval is already implemented.
- Default weighting is:
  - dense embeddings: `0.7`
  - BM25: `0.3`
- Web UI allows changing:
  - `top_k` from `0` to `50`
  - dense/BM25 weighting
  - minimum score
  - minimum relative score to the best chunk
  - retrieve-only mode
  - LLM model
- `top_k=0` intentionally disables retrieval.

## Current UX features already implemented

- Dark mode
- Help modal
- Health icon button
- Local browser history stored in `localStorage`
- Expandable source chunks
- Highlighting of query terms inside source excerpts and full chunks
  - this is lexical highlighting based on the current question
  - it is not an explanation of embedding similarity

## Prompting behavior

- Prompt is in `app/rag/prompts.py`.
- The model is asked to:
  - answer naturally in the language of the question, usually Czech
  - separate sourced information from general knowledge and uncertainty
  - cite only sources actually used
  - not always start with a rigid template like `Podle nalezených zdrojů...`
- For clearly non-historical questions:
  - respond briefly and naturally
  - mention it is primarily a historical assistant
  - do not force citations if they are not relevant

## Special data handling: WP1 subset

- `data/raw/WP1-2026-02-subset/` contains nested folders with PDFs and `meta.md`.
- Ingestion was extended to parse these folder-level metadata files.
- For WP1 files, the UI should show generated storage links in the source panel.
- URL pattern is based on the relative file path under:
  - `data/raw/WP1-2026-02-subset/`
- The generated document link format is:

```text
https://storage.ufal.mff.cuni.cz/lib/2e093cea-cdcd-401d-a664-d1ca05112e55/file/v2026-02/<folder>/<filename>
```

- Source paths shown in UI should omit the `data/raw/` prefix.

## Wikipedia downloader behavior

- `scripts/download_wikipedia.py`:
  - uses a curated fallback topic list first
  - then searches based on `questions.txt`
  - prints light progress logging
  - skips files already present in the target directory
- This is only test-data tooling. The project should not become Wikipedia-dependent.

## Logging

- Every new run creates a fresh timestamped log file under `logs/`.
- This is already wired for:
  - API
  - ingest script
  - ask script
  - Wikipedia downloader
- Third-party noise was reduced to keep logs usable.

## Shutdown cleanup

- The pipeline and vector store have explicit `close()` methods.
- FastAPI lifespan in `app/main.py` closes the pipeline on shutdown.
- This was added because Ctrl+C used to trigger a leaked semaphore warning.
- If that warning returns, also check whether `uvicorn --reload` is the actual source.

## Re-ingestion rules

You should re-run ingestion if:

- documents in `data/raw/` changed
- `EMBEDDING_MODEL` changed
- chunking parameters changed
- metadata parsing behavior changed
- `data/raw/agent.md` changed and should become retrievable

Do not mix vectors from different embedding models in one collection.

## Identity document

- `data/raw/agent.md` exists on purpose.
- It gives the assistant a grounded answer to questions like `Kdo jsi?`
- If it is edited, re-ingest.

## Files worth checking first when debugging

- `app/rag/pipeline.py`
- `app/rag/retrieval.py`
- `app/rag/documents.py`
- `app/rag/prompts.py`
- `app/rag/vector_store.py`
- `app/static/app.js`
- `app/static/styles.css`
- `app/main.py`

## Current model presets in the API

Defined in `app/main.py`:

- `openai/gpt-5.2`
- `openai/gpt-5.4-mini`
- `meta-llama/llama-3.3-70b-instruct`
- `meta-llama/llama-3.1-8b-instruct`
- `openai/gpt-4o-mini`
- `openai/gpt-4.1-mini`
- `anthropic/claude-3.5-haiku`
- `google/gemini-2.0-flash-001`
- `google/gemini-3.0-pro`
- `mistralai/mistral-small-3.1-24b-instruct`

## Nice next improvements

- Show the most relevant sentence window around matches, not just raw chunk previews
- Streaming responses in the frontend
- Better semantic explanation of why a chunk matched
- Optional reranker after hybrid retrieval
- More robust evaluation scripts for grounding quality
