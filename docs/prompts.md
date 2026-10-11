# Prompts, placeholders, and work packages

Work packages scope built-in prompts, collections, and optional prepared questions. The definitions live in `app/rag/wp_config.py`.

## Prompts And Placeholders

The app picks a **WP** first; that scopes which prompts and collections you see. Selecting a WP loads its default prompt and collection.

### Prompts: local vs shared

A prompt is one concept to the UI (the dropdown merges built-ins + local + shared), but has two storage lifecycles:

- **Built-in prompts** ship read-only in code (`app/rag/wp_config.py`), including the WP1 personas (`Učitel`/`Historik`/`Laik`). Editing their prompt text is a **save as new**. An administrator can attach a transformation-only override to a built-in prompt from Settings without copying or replacing its prompt text.
- **Local prompts** live in browser `localStorage` (key `czdemos4ai-local-prompt-presets`). They are private to that browser and need no password to edit or delete.
- **Shared/server prompts** live in `data/prompt_presets.json` (gitignored mutable overlay; may be absent). The same file stores built-in transformation overrides under `builtin_overrides`; these are merged onto the code-defined prompt at runtime. Creating a shared prompt is open. Updating or deleting one requires either an `owner_id` match (the browser that created it) or the shared `ADMIN_PASSWORD`; changing a built-in override always requires the admin password.

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

## Random Questions

The "Náhodná otázka" button (`GET /questions/random?wp_id=...`) and the "Připravené otázky" dropdown (`GET /questions?wp_id=...`) read a per-WP plain-text file (one question per line) configured by `questions_path` in `app/rag/wp_config.py`:

- `data/questions/wp1-historie.txt`
- `data/questions/wp2-media.txt`
- `data/questions/wp3-pravo.txt`
- `data/questions/wp4-adiktologie.txt`

These files are **private and gitignored** (`data/questions/` in `.gitignore`), so they are not in the repo. They must be provisioned separately on each machine/deploy (rsync, mounted volume, or your data-deploy step). When a WP's file is missing, `GET /questions/random` and `GET /questions` return a localized 404 and the rest of the app keeps working — only that WP's random-question button and prepared-questions dropdown are unavailable.

## Collections And Prompts

For the local reference implementation, `data/raw/` holds documents to ingest. Built-in prompts and placeholder defaults ship in code (`app/rag/wp_config.py`, `app/rag/placeholders.py`). The Czech-history app metadata and UI assets are kept under `data/collections/czech_history/`.

The current Czech-history setup also uses these assets:

- topic list: `topics/topics.txt`
- UFAL logo asset: `app/static/logo_ufal_110u.png`

Random-question seed files have moved to the private, per-WP files under `data/questions/` (see [Random Questions](#random-questions)).

## Answer Grounding

The prompt instructs the model to separate:

- claims supported by retrieved chunks,
- general historical knowledge,
- uncertainty or insufficient coverage in the retrieved documents.

The model should first decide whether retrieved chunks are actually relevant. It should cite only chunks that support the answer, avoid forced citations from weak matches, and may add general historical context without pretending it came from the retrieved documents.

The answer cites retrieved chunks with Markdown footnotes. In the answer text these appear as simple footnote numbers, while the generated source list keeps stable source ids such as `[Z1]`, `[Z2]`, etc. The frontend displays source metadata and excerpts, highlights cited sources on the right, and lets you expand retrieved chunks.

## WP configuration and preset records

- WPs are typed dataclasses in `wp_config.py`, not env or JSON — add or change one there. WP1 holds the Czech-history prompts; WP2–WP4 ship neutral starters.
- Collections map by number prefix (WP1→`wp1-*`, etc.). `wp_config.py` entries are only the offline fallback; at runtime `MSearchRetriever.live_collections_by_prefix()` lists live versions (refreshed daily in the background, busted by `/llm-providers/refresh`), injected into `/settings` by `_wps_payload_with_live_collections()` in `main.py`.
- AI-Ufal gating is per-WP (`WPConfig.requires_aiufal`, currently WP2). Backend `_enforce_msearch_collection_policy` gates by `wp_id`; frontend disables gated collections unless AI Ufal provider is selected.
- Random/prepared questions are per-WP plain-text files configured by `WPConfig.questions_path`: `data/questions/wp1-historie.txt`, `wp2-media.txt`, `wp3-pravo.txt`, `wp4-adiktologie.txt`. These are private/gitignored; missing files make `/questions/random` and `/questions` return 404 for that WP only.
- `/settings` exposes `wps` + `default_wp`; built-in prompts appear even without `data/prompt_presets.json`.
- Preset JSON shape (shared file + browser `localStorage`): `{id, name, wp_id, note, system_prompt, user_prompt_template, placeholders, owner_id, updated_at}`. `note` is user-facing metadata and is never sent to the model. Every preset stores `wp_id`; unknown/missing falls back to default WP. The loader tolerates malformed files.


## Prompting implementation

- Base prompt helpers live in `app/rag/prompts.py`; WP-specific built-in prompts live in `app/rag/wp_config.py`. Read the prompts there before changing behaviour — among other things they tell the model to answer in the question's language, to cite only sources it used, and not to write its own closing source list or `[^Zn]:` footnote definitions.
- Models emit that closing list anyway. `strip_model_source_list` (`app/rag/answer_cleanup.py`) removes it server-side; `prepareCitationMarkdown` (`frontend/citations.js`) does the same at render time for streaming tokens. Keep the two in sync — `tests/test_answer_cleanup.py` is the shared contract.
