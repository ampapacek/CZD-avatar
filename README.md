# rag-avatar

`rag-avatar` is a web app for asking questions over a document collection. It finds relevant source passages, streams an answer, shows the retrieved documents beside the answer, and keeps citations visible so you can inspect what the answer is based on.

The current default setup is a Czech-history avatar. A few places are still hardcoded for the historical agent and Czech-history collection, especially default prompts, random questions, UI text, collection assets, and helper scripts. The underlying RAG pipeline is topic-agnostic, though: with different documents, retrieval settings, and prompts it can be used for other domains.

## Quick Start

Use Python 3.12. The system `python` command may not exist on this machine, so the examples use `uv`.

```bash
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

Edit `.env`.

For the default hosted `msearch` flow, you typically only need:

```env
LLM_API_KEY=your_key_here
LLM_MODEL=openrouter/free
RETRIEVAL_BACKEND=msearch
MSEARCH_USERNAME=your_username
MSEARCH_PASSWORD=your_password
```

`MSEARCH_BASE_URL`, `MSEARCH_COLLECTION`, `MSEARCH_MODE`, and the other mSearch defaults are already present in `.env.example`.

## LLM Providers

Generation uses an OpenAI-compatible chat-completions API. You can point the app at any compatible provider by setting:

```env
LLM_BASE_URL=https://your-provider.example/v1
LLM_API_KEY=your_provider_key
LLM_MODEL=provider/model-or-local-model-name
```

The variable names are now generic `LLM_*`. `OPENROUTER_*` is still accepted as a backward-compatible alias during migration. In the web UI, the `LLM API` panel can also override the base URL and API key for the current browser session, and the model selector supports a custom model id.

If you want to limit the shared server key to only a safe or free model, set `LLM_PUBLIC_MODELS` in `.env`. The simplest option is `openrouter/free`, which routes requests to currently available free models on OpenRouter. The web UI will then allow that model without an API key, while any other model will require the user to enter their own key in the browser.

## Run The App

Start the API and frontend:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

The default experience uses hosted `msearch` retrieval, so you can run the app without ingesting local documents first.

## Ask A Question

From the browser, try a Czech-history question such as:

- `Jaký byl význam husitských válek?`
- `Co znamenalo Pražské jaro?`

From the CLI:

```bash
uv run python scripts/ask.py "Jaký byl význam husitských válek?"
```

Optional controls:

```bash
uv run python scripts/ask.py "Co znamenala bitva na Bílé hoře pro české země?" --style historik --length long --custom-instructions "Zaměř se na příčiny a důsledky."
```

## Use A Local Database Instead

If you want to use local Qdrant + BM25 retrieval instead of hosted `msearch`, do this:

1. Set `RETRIEVAL_BACKEND=local` in `.env`.
2. Put your `.txt`, `.md`, or `.pdf` files under `data/raw/`.
3. Ingest the files into the local index.
4. Run the app or ask questions from the CLI.

Example:

```env
RETRIEVAL_BACKEND=local
```

```bash
uv run python scripts/ingest.py --path data/raw
uvicorn app.main:app --reload
```

The ingest step creates/updates:

- local Qdrant storage in `data/qdrant/`
- BM25/debug chunk catalog in `data/processed/chunks.jsonl`

## Add Local Documents

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
uv run python scripts/download_wikipedia.py --limit 100
```

The script reads `data/collections/czech_history/questions/questions.txt`, searches Czech Wikipedia, and saves Markdown files with metadata into `data/raw/wikipedia/`.

## Ingest Local Documents

```bash
uv run python scripts/ingest.py --path data/raw
```

This creates/updates:

- local Qdrant storage in `data/qdrant/`
- BM25/debug chunk catalog in `data/processed/chunks.jsonl`

## API

API endpoints:

- `GET /health`
- `GET /settings`
- `GET /questions/random`
- `GET /prompt-presets`
- `POST /prompt-presets`
- `DELETE /prompt-presets/{preset_id}`
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
  "retrieval_backend": "msearch",
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
- retrieval backend: `msearch` or `local`
- mSearch collection, mode, and optional confidence floor
- retrieve-only mode, which shows chunks without calling the LLM
- LLM model preset or custom model id
- optional custom OpenAI-compatible LLM base URL and API key in the `LLM API` panel
- editable prompt presets stored in `data/prompt_presets.json`

## Configuration

Important `.env` variables:

- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_BASE_URL`
- `OPENROUTER_API_KEY` as a backward-compatible alias
- `OPENROUTER_MODEL` as a backward-compatible alias
- `OPENROUTER_BASE_URL` as a backward-compatible alias
- `LLM_PUBLIC_MODELS`
- `QDRANT_URL` for a remote/server Qdrant; leave empty for local disk mode
- `QDRANT_PATH`
- `QDRANT_COLLECTION`
- `EMBEDDING_MODEL`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`
- `TOP_K`
- `MIN_SCORE`
- `MIN_RELATIVE_SCORE`
- `RETRIEVAL_BACKEND`
- `MSEARCH_BASE_URL`
- `MSEARCH_USERNAME`
- `MSEARCH_PASSWORD`
- `MSEARCH_COLLECTION`
- `MSEARCH_MAX_RESULTS`
- `MSEARCH_MODE`
- `MSEARCH_MIN_CONFIDENCE`
- `MSEARCH_TIMEOUT`
- `DEFAULT_STYLE`
- `DEFAULT_LENGTH`
- `RAW_DATA_DIR`
- `CHUNK_CATALOG_PATH`
- `PROMPT_PRESETS_PATH`

## Basic Test Run

```bash
uv run python scripts/download_wikipedia.py --limit 20
uv run python scripts/ingest.py --path data/raw
uv run python scripts/ask.py "Jaký byl význam husitských válek?"
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

For now, `data/raw/` acts as the active indexed document collection and `app/rag/prompts.py` contains the built-in default prompts. Saved prompt presets are stored in `data/prompt_presets.json`. The Czech-history app metadata and UI assets are kept under `data/collections/czech_history/`.

Collection-specific app assets currently live under `data/collections/czech_history/`:

- random-question seed file: `questions/questions.txt`
- extended question set: `questions/questions_extended.txt`
- topic list: `topics/topics.txt`
- UFAL logo asset: `assets/logo_ufal_110u.png`

The app can be adapted to any topic, but this is not fully configuration-driven yet. When creating a new avatar/domain, check and update the default prompts, random-question file, frontend labels, collection asset paths in `app/main.py`, example questions, and any collection-specific helper scripts. Future versions should make collections and prompts selectable, for example by using separate folders/config files per avatar.

## Notes For Future Extensions

- Use `LLM_BASE_URL` with an Ollama/vLLM/OpenAI-compatible local server or another hosted OpenAI-compatible provider.
- Add a cross-encoder reranker after hybrid retrieval.
- Add richer metadata extraction for your real historical archive.
- Add evaluation sets and automated citation-grounding checks.
- Add selectable collections and system prompts for different avatars.
