# CZD-avatar

CZD-avatar is a web app for asking questions over document collections in the
[CZDEMOS4AI project](https://prg.ai/projekty/czdemos4ai/). It retrieves source
passages, streams an answer, and shows citations and documents for inspection.

**The current setup requires access to the private mSearch service from MAMA AI
and an OpenAI-compatible LLM provider.** Cloning this repository alone is not
enough to use the supported setup. The main audience is ÚFAL colleagues and
deployment operators.

The app provides prompts, configurable placeholders, model selection,
conversation mode, browser history, and answer sharing. It is organized around
four work packages:

- WP1: history
- WP2: media
- WP3: law
- WP4: addiction studies

WP1 includes Czech-history prompts and assets; the other work packages include
neutral starter prompts. Retrieval and collection configuration remain tied to
mSearch, so the app does not currently offer a general interface for arbitrary
retrieval backends.

## Requirements

- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- mSearch credentials and access to the relevant collections
- An API key for an OpenAI-compatible LLM provider

Node.js is needed only for frontend development. The repository includes the
built frontend bundle.

## Quick start

Create a virtual environment and install the app:

```bash
uv venv --python python3.12
source .venv/bin/activate
uv pip install -e .
cp .env.example .env
```

Edit `.env` with your mSearch and LLM provider credentials. See
[Configuration and LLM providers](docs/configuration.md) for details.

Start the app:

```bash
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

Select a work package, collection, model, and prompt, then ask a question.
For WP1, try `Jaký byl význam husitských válek?` and inspect the answer's
citations and retrieved passages. Ask a question weakly covered by the collection
and check whether the answer makes its limited evidence clear.

Prepared and random questions require private per-WP files under
`data/questions/`. These files are optional and are not included in the repository.

## Development and tests

See [Architecture and development](docs/architecture.md) for development setup,
tests, and frontend builds.

## Documentation

- [Configuration and LLM providers](docs/configuration.md)
- [Prompts, placeholders, and work packages](docs/prompts.md)
- [Retrieval, reranking, and local reference implementation](docs/retrieval.md)
- [Usage analytics and logging](docs/analytics.md)
- [Deployment](docs/deployment.md)
- [Architecture and development conventions](docs/architecture.md)
