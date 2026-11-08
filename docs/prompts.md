# Prompts, placeholders, and work packages

Work packages scope built-in prompts, collections, and optional prepared questions. They are defined per server in the instance config file (`INSTANCE_CONFIG_PATH`, see [Instance config](#instance-config)); the code knows no specific WP.

## Prompts And Placeholders

The app picks a **WP** first; that scopes which prompts and collections you see. Selecting a WP loads its default prompt and collection.

### Prompts: local vs shared

A prompt is one concept to the UI (the dropdown merges built-ins + local + shared), but has two storage lifecycles:

- **Built-in prompts** are read-only and come from the instance config file (`[[wps.prompts]]`). Editing their prompt text is a **save as new**. An administrator can attach a transformation-only override to a built-in prompt from Settings without copying or replacing its prompt text.
- **Local prompts** live in browser `localStorage` (key `czdemos4ai-local-prompt-presets`). They are private to that browser and need no password to edit or delete.
- **Shared/server prompts** live in `data/prompt_presets.json` (gitignored mutable overlay; may be absent). The same file stores built-in transformation overrides under `builtin_overrides`; these are merged onto the configured built-in prompt at runtime. The instance config can switch shared presets off (`shared_presets = false`): `/prompt-presets` then lists none and refuses saving and deleting, and the UI hides `Sdílet s ostatními`. Creating a shared prompt is open. Updating or deleting one requires either an `owner_id` match (the browser that created it) or the shared `ADMIN_PASSWORD`. The owner id is never returned: lists take the browser's `?owner_id=` and mark its own records with `mine: true`; changing a built-in override always requires the admin password.

### Placeholders

Every user-facing template variable is a declared **placeholder**, written as `{name}` in a prompt. Two groups:

- **System placeholders** — filled automatically by the server, no control: `{question}`, `{retrieved_snippets}`, `{current_date}` (server-local date).
- **Parameter placeholders** — surfaced as a control on the main page, data-driven from the tokens the selected prompt uses. Each has a `kind`:
  - `select` — named options `{name, label, text}`; substitutes the chosen option's `text` (e.g. `{length}` → short/medium/long).
  - `text` — free text; substitutes the typed string, or a `default` when empty (e.g. `{custom_instructions}` → `Žádné.`). Omitted if the placeholder is absent from the template.

A placeholder definition is taken **wholesale** from the most specific source that declares it (options are never merged across sources). Resolution order, most specific first:

1. **inline on the selected prompt** (a preset's or built-in's inline `placeholders` map)
2. **browser-local global defs** (`localStorage` key `czdemos4ai-local-placeholder-defs`)
3. **shared overlay** (`data/placeholders.json`, gitignored mutable overlay; may be absent; edits need `owner_id` or `ADMIN_PASSWORD`)
4. **code-default floor** (`DEFAULT_PLACEHOLDERS` in `app/rag/placeholders.py`, ships `length` + `custom_instructions`)
5. otherwise the token is **undeclared**: it renders literally and the UI warns — it never crashes.

The chat request carries `selections` (a generic `{name: value}` map) and `placeholder_defs` (the frontend's fully-resolved effective defs for the placeholders the prompt uses), so the server is stateless about `localStorage` and substitutes exactly what the browser configured.

> Inline placeholder defs edited on a **server** preset persist only when the prompt is saved; the UI shows an amber warning until then.

Browser state lives in `localStorage`. Important keys include `czdemos4ai-local-prompt-presets`, `czdemos4ai-local-placeholder-defs`, `czdemos4ai-history-v2`, `czdemos4ai-conversations`, `czdemos4ai-llm-settings`, `czdemos4ai-token-budget`, `czdemos4ai-browser-owner-id`, and `theme`.

## Answering without sources

The Kolekce selector ends with **Bez zdrojů**, which turns retrieval off. It behaves exactly like `top_k=0` (Dokumentů: 0): no retrieval, no conversation query rewrite (`retrieval_query_rewrite_skip_reason: "no_sources"`), no Sources panel, and `Pouze vyhledat zdroje` and `Kopírovat se zdroji` are hidden; Bez zdrojů also disables the retrieval sliders. Query transformations still run. With retrieval off no collection content goes to the provider, so the per-WP provider restriction (`allowed_providers`) does not apply.

- **The profile stays the same.** Whenever nothing is retrieved (Bez zdrojů, `top_k=0`, or a search that finds nothing) `{retrieved_snippets}` renders as `NO_SOURCES_CONTEXT` in `app/rag/prompts.py`: "Nebyly nalezeny žádné zdroje. Odpověz podle svých znalostí." Empty prompt texts fall back to the defaults as usual.
- **A prompt without `{retrieved_snippets}`** (in either text; an empty text counts as the default) has no use for sources, so while it is active the UI switches Kolekce to Bez zdrojů and locks it, with a note under Profil. The next prompt with sources restores the collection it replaced (the WP's default after a WP switch). The prompt editor shows a note when the variable is missing. There is no per-prompt flag; the mode follows from the text.
- A topic-neutral built-in such as `Obecný asistent` is an ordinary prompt in the instance config whose texts leave out `{retrieved_snippets}`; a server offers one only if its file defines it.
- The request carries `use_sources: false`. The mode is stored as the sentinel collection value `__no_sources__` wherever the collection already is (conversation settings, history entries), so restoring them restores the mode. Conversation turns follow the current setting, so one thread can mix turns with and without sources.
- CLI: `uv run python scripts/ask.py "…" --no-sources` (same as `--top-k 0`).

## Random Questions

The "Náhodná otázka" button (`GET /questions/random?wp_id=...`) and the "Připravené otázky" dropdown (`GET /questions?wp_id=...`) read the WP's `questions` list from the instance config. A WP without questions (or an unknown `wp_id`) returns a 404 and only that WP's question buttons are unavailable.

## Collections And Prompts

For the local reference implementation, `data/raw/` holds documents to ingest. Built-in prompts come from the instance config; placeholder defaults ship in code (`app/rag/placeholders.py`). The Czech-history app metadata and UI assets are kept under `data/collections/czech_history/`.

The current Czech-history setup also uses these assets:

- topic list: `topics/topics.txt`
- UFAL logo asset: `app/static/logo_ufal_110u.png`

## Answer Grounding

The prompt instructs the model to separate:

- claims supported by retrieved chunks,
- general historical knowledge,
- uncertainty or insufficient coverage in the retrieved documents.

The model should first decide whether retrieved chunks are actually relevant. It should cite only chunks that support the answer, avoid forced citations from weak matches, and may add general historical context without pretending it came from the retrieved documents.

The answer cites retrieved chunks with Markdown footnotes. In the answer text these appear as simple footnote numbers, while the generated source list keeps stable source ids such as `[Z1]`, `[Z2]`, etc. The frontend displays source metadata and excerpts, highlights cited sources on the right, and lets you expand retrieved chunks.

## Instance config

Each server has one TOML file, named by `INSTANCE_CONFIG_PATH` in `.env`, that lists the WPs it offers. [`instance.example.toml`](../instance.example.toml) in the repo root documents every field; real files live in `data/instances/` (gitignored) and are copied to each server by hand. Without a valid file the app refuses to start and says what to set.

- TOML because the prompts are long multi-line Czech texts: literal strings (`'''...'''`) keep them verbatim, without escapes, and the file can carry comments. The file is read-only for the app; runtime state it writes (`data/prompt_presets.json`, `data/placeholders.json`) stays JSON. Restart the app after editing.
- Loading and validation are in `app/rag/wp_config.py` (`load_instance_config`). Unknown keys, duplicate WP or prompt ids, a default prompt or collection that the WP does not define, and an `allowed_providers` id that `LLM_PROVIDERS` does not configure are startup errors.
- What the file defines is what the server offers. The first WP is the default. With a single WP the UI hides every WP selector (main page, conversation settings, Settings, history filter, cache dialogs).
- Collections: `[[wps.collections]]` entries are the offline fallback and the preferred default. At runtime `MSearchRetriever.live_collections_by_prefix()` lists the live mSearch collections whose name starts with a WP's `collection_prefix` followed by `-` (refreshed daily in the background, busted by `/llm-providers/refresh`), injected into `/settings` by `_wps_payload_with_live_collections()` in `main.py`.
- Provider restriction: `allowed_providers` on a WP lists the only provider ids that may receive its collection content. `_enforce_msearch_collection_policy` checks it by `wp_id` and by collection id (configured ids plus the live collections under the WP's prefix), so a forged `wp_id` cannot smuggle a restricted collection through another WP. A request matches a provider only with its id and its configured base URL, so a custom URL never passes. The frontend disables the restricted collections for other providers. Without retrieval (Bez zdrojů, `top_k=0`) the restriction does not apply.
- `/chat`, `/chat/stream` and saving a shared preset refuse a `wp_id` the file does not define; `/questions` answers 404.
- `/settings` exposes `wps`, `default_wp` and `shared_presets`; built-in prompts appear even without `data/prompt_presets.json`.
- Tests use the synthetic `tests/fixtures/instance.toml` (wired in `tests/conftest.py`), never a real file.

## Preset records

- Preset JSON shape (shared file + browser `localStorage`): `{id, name, wp_id, note, system_prompt, user_prompt_template, placeholders, owner_id, updated_at}`. `note` is user-facing metadata and is never sent to the model. Every preset stores `wp_id`; a missing one falls back to the default WP. A `wp_id` the server does not define is kept (the file may be shared by servers that offer different WPs), so such presets are simply not listed under any WP there. The loader tolerates malformed files.


## Prompting implementation

- Base prompt helpers live in `app/rag/prompts.py`; the built-in prompts live in each server's instance config file. Read the prompts there before changing behaviour — among other things they tell the model to answer in the question's language, to cite only sources it used, and not to write its own closing source list or `[^Zn]:` footnote definitions.
- Models emit that closing list anyway. `strip_model_source_list` (`app/rag/answer_cleanup.py`) removes it server-side; `prepareCitationMarkdown` (`frontend/citations.js`) does the same at render time for streaming tokens. Keep the two in sync — `tests/test_answer_cleanup.py` is the shared contract.
