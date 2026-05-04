# rag-avatar

A practical RAG chatbot/avatar MVP. It ingests local document collections, retrieves relevant passages with Qdrant plus BM25, and generates source-grounded answers through an OpenAI-compatible API such as OpenRouter.

The current default setup is a Czech-history avatar. The code is structured so later versions can use different document collections, different metadata, and different system prompts.

Collection-specific app assets currently live under `data/collections/czech_history/`:

- random-question seed file: `questions/questions.txt`
- extended question set: `questions/questions_extended.txt`
- topic list: `topics/topics.txt`
- UFAL logo asset: `assets/logo_ufal_110u.png`

## Setup

Use Python 3.12. The system `python` command may not exist on this machine, so the examples use `uv`.

```bash
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

Edit `.env` and set:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
```

## Add Documents

Put `.txt`, `.md`, or `.pdf` files under:

```text
data/raw/
```

Text and Markdown files may include simple metadata frontmatter:

```md
---
title: Bitva na Bílé hoře
url: https://example.org/source
source_name: archive
document_type: article
historical_period: raný novověk
---

Document text...
```

## Czech Wikipedia Test Data

Czech Wikipedia is only for testing the current Czech-history collection before your own document collection is ready.

```bash
python scripts/download_wikipedia.py --limit 100
```

The script reads `data/collections/czech_history/questions/questions.txt`, searches Czech Wikipedia, and saves Markdown files with metadata into `data/raw/wikipedia/`.

## Ingest

```bash
python scripts/ingest.py --path data/raw
```

This creates/updates:

- local Qdrant storage in `data/qdrant/`
- BM25/debug chunk catalog in `data/processed/chunks.jsonl`

## Ask From CLI

```bash
python scripts/ask.py "Jaký byl význam husitských válek?"
```

Optional controls:

```bash
python scripts/ask.py "Co znamenala bitva na Bílé hoře pro české země?" --style historik --length long --custom-instructions "Zaměř se na příčiny a důsledky."
```

## Run API And Frontend

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API endpoints:

- `GET /health`
- `GET /settings`
- `GET /questions/random`
- `POST /ingest`
- `POST /retrieve`
- `POST /chat`
- `POST /chat/stream`

Example `/chat` body:

```json
{
  "question": "Jaký byl význam husitských válek?",
  "style": "ucitel",
  "length": "medium",
  "custom_instructions": "Focus mainly on causes and consequences."
}
```

## Answer Grounding

The prompt instructs the model to separate:

- claims supported by retrieved chunks,
- general historical knowledge,
- uncertainty or insufficient coverage in the retrieved documents.

The model should first decide whether retrieved chunks are actually relevant. It should cite only chunks that support the answer, avoid forced citations from weak matches, and may add general historical context without pretending it came from the retrieved documents.

The answer cites retrieved chunks with Markdown footnotes. In the answer text these appear as simple footnote numbers, while the generated source list keeps stable source ids such as `[Z1]`, `[Z2]`, etc. The frontend displays source metadata and excerpts, highlights cited sources on the right, and lets you expand retrieved chunks.

## Retrieval Controls

The web UI lets you tune retrieval while testing:

- `top-k` from 0 to 50
- embedding vs. BM25 weighting
- minimum combined score
- minimum score relative to the best retrieved chunk
- retrieve-only mode, which shows chunks without calling the LLM
- OpenRouter model preset or custom model id

## Configuration

Important `.env` variables:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`
- `QDRANT_URL` for a remote/server Qdrant; leave empty for local disk mode
- `QDRANT_PATH`
- `QDRANT_COLLECTION`
- `EMBEDDING_MODEL`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `TOP_K`
- `MIN_SCORE`
- `MIN_RELATIVE_SCORE`
- `DEFAULT_STYLE`
- `DEFAULT_LENGTH`
- `RAW_DATA_DIR`
- `CHUNK_CATALOG_PATH`

## Basic Test Run

```bash
python scripts/download_wikipedia.py --limit 20
python scripts/ingest.py --path data/raw
python scripts/ask.py "Jaký byl význam husitských válek?"
uvicorn app.main:app --reload
```

Then test in the browser:

- style `učitel`, length `medium`
- question `Jaký byl význam husitských válek?`
- confirm the answer is Czech and shows citations
- ask a question weakly covered by the indexed files and confirm the answer marks limited evidence

## Logs

Each server or script start creates a new timestamped log file in:

```text
logs/
```

Examples:

```text
logs/api-20260424-104255.log
logs/ingest-20260424-104501.log
logs/ask-20260424-104712.log
logs/download-wikipedia-20260424-104900.log
```

Console output stays shorter, while the file logs persist questions, retrieval metadata, selected model, response timing, and generated answers.

## Collections And Prompts

For now, `data/raw/` acts as the active indexed document collection and `app/rag/prompts.py` contains the default system prompt. The Czech-history app metadata and UI assets are kept under `data/collections/czech_history/`. Future versions should make collections and prompts selectable, for example by using separate folders/config files per avatar.

## Notes For Future Extensions

- Replace `OpenAICompatibleLLM` with an Ollama/vLLM/OpenAI-compatible local server client.
- Add a cross-encoder reranker after hybrid retrieval.
- Add richer metadata extraction for your real historical archive.
- Add evaluation sets and automated citation-grounding checks.
- Add selectable collections and system prompts for different avatars.
