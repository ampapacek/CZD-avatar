# Prompt Preset Refactor Plan

## Goal

Replace the current `profile/style + prompt fragments` model with a clearer `Prompt + Length` model.

Users should choose a prompt preset on the main page. A prompt preset represents a full assistant profile, such as `Ucitel`, `Historik`, `Laik`, or a future WP-specific prompt. Each preset can define both:

- system prompt: stable assistant behavior, citation policy, tone, and domain rules
- user prompt template: how `{question}`, `{context}`, and `{custom_instructions}` are packaged for each request

Length stays separate and orthogonal. Each prompt preset can define its own meanings for `{length}` values such as short, medium, and long.

This plan intentionally keeps the future WP/avatar selector out of the first implementation, but prepares the model so prompts can later be grouped by WP/avatar and shown only with relevant collections.

## Principles

- Keep each step as a vertical, testable slice.
- Preserve backward compatibility where practical, especially for existing saved prompt presets.
- Make the normal UI simple: users should see `Prompt` and `Length`, not internal prompt fragments.
- Keep advanced controls available for editing the user prompt template.
- Treat server prompts as shared and local prompts as browser-private.
- Require one shared admin password for modifying or deleting server prompts owned by another browser.
- Built-in prompts are read-only; editing one should require saving a local or shared copy.
- Server prompt creation stays open for now, but updating/deleting protected shared prompts requires ownership or the admin password.

## Task 1: Prompt Text Cleanup Without Data Model Changes

Status: Done.

Scope:

- Move profile-specific rules out of the base system prompt.
- Make the base/default system prompt shorter and more generic.
- Keep the existing `style` selector and API shape for this step.
- Update the existing `STYLE_PROMPTS` so `ucitel`, `historik`, and `laik` contain their own complete behavior around citation strictness, general knowledge, and uncertainty.
- Rename visible historical-only wording to neutral `Avatar` where it is clearly app-level copy and not WP1-specific content.

Why first:

- This immediately fixes the confusing instruction Martin noticed.
- It is low risk because it does not change request/response models or saved preset structure.

Verification:

- Run unit tests and compile check.
- Start the app and confirm the default chat still sends a rendered prompt with no literal unresolved `{style}` or `{length}`.
- Manually inspect generated request payloads in the browser console or backend logs if needed.

Expected commit:

- `clarify profile prompt responsibilities`

## Task 2: Add Prompt Preset Selection To The Main Page

Scope:

- Add a `Prompt` dropdown to the main chat controls.
- Populate it with the built-in default plus existing server prompt presets.
- Selecting a prompt loads its system prompt, user prompt template, and length prompt definitions into the active chat settings.
- Keep the existing profile selector temporarily, but visually de-emphasize it or keep it only as a compatibility control for this step.
- Ensure saved conversation/history entries capture the selected prompt state.

Why this slice:

- Users can finally choose saved prompts without opening Settings.
- The old profile model still exists underneath, so the step can be tested independently.

Verification:

- Start the app.
- Select `Default` and ask a question.
- Select a saved preset and ask the same question.
- Confirm the outgoing chat request contains the selected preset prompt fields.
- Confirm local conversation restore keeps the prompt selection.

Expected commit:

- `add main prompt preset selector`

## Task 3: Split Save Actions Into New, Save As, Update, And Delete

Scope:

- Replace the single ambiguous `Ulozit` behavior in Settings with explicit actions:
  - `New blank`
  - `Save as new`
  - `Update selected`
  - `Delete`
- `New blank` clears system prompt, user prompt template, and length definitions.
- `Save as new` always creates a new prompt preset.
- `Update selected` only updates the selected existing preset.
- Keep server-only persistence for this task; local prompt storage comes next.

Why this slice:

- It fixes the immediate overwrite confusion without changing storage ownership yet.

Verification:

- From `Default`, create a new preset and confirm it appears as a new item.
- From an existing preset, use `Save as new` and confirm it does not overwrite the original.
- From an existing preset, use `Update selected` and confirm only that preset changes.
- Delete an existing preset and confirm it disappears.

Expected commit:

- `make prompt preset save actions explicit`

## Task 4: Convert Profile Into Prompt Presets

Scope:

- Replace the main-page `Profil` selector with the `Prompt` selector.
- Create built-in prompt presets for the current profiles:
  - `Laik`
  - `Ucitel`
  - `Historik`
- Each built-in prompt preset contains a full system prompt and a user prompt template.
- Keep `Length` as a separate selector.
- Keep request compatibility by still accepting old `style` values if present, but make new frontend requests use selected prompt fields instead.
- Hide or remove style prompt editing from Settings.

Why this slice:

- This is the conceptual switch from `profile + style fragment` to `prompt preset`.
- It is testable because built-in prompts should reproduce the old profile behaviors.

Verification:

- Ask with `Ucitel`, `Historik`, and `Laik` prompts and confirm the backend receives different full system prompts.
- Confirm no new request depends on `style_prompts`.
- Confirm old saved entries with style data still load without crashing.

Expected commit:

- `replace profiles with prompt presets`

## Task 5: Per-Prompt Length Definitions

Scope:

- Treat `length_prompts` as part of each prompt preset.
- When a prompt is selected, its length definitions become active.
- When a prompt lacks length definitions, fall back to the app defaults.
- In Settings, show short, medium, and long length definition fields for the selected prompt.
- Keep `{length}` as a supported placeholder in system prompts and user prompt templates.

Why this slice:

- It implements Martin's point that short/medium/long can mean different things for each prompt or future WP.

Verification:

- Set a custom `short` definition on one prompt.
- Ask using that prompt with `short` and confirm the rendered prompt includes the custom definition.
- Switch to another prompt and confirm it uses its own length definitions or defaults.

Expected commit:

- `support per-prompt length definitions`

## Task 6: Template Variable Handling

Scope:

- Keep support for known variables:
  - `{question}`
  - `{context}`
  - `{custom_instructions}`
  - `{length}`
- If a prompt does not contain `{custom_instructions}`, do not force custom instructions into the rendered prompt.
- If `{custom_instructions}` is present and the user left it empty, render a neutral default such as `Zadne.`
- If an unknown placeholder appears, allow saving with a visible warning and render the placeholder literally.
- Add room for future known variables such as `{current_date}` without introducing a full templating language.

Why this slice:

- It makes prompt editing understandable and avoids accidental broken prompts.

Verification:

- Test prompts with and without `{custom_instructions}`.
- Test empty custom instructions.
- Test a prompt containing an unknown placeholder and confirm the app warns but does not crash.

Expected commit:

- `make prompt template variables explicit`

## Task 7: Local Browser Prompt Presets

Scope:

- Add local prompt presets stored in `localStorage`.
- Show local and server prompts in one dropdown.
- Use minimal labels or grouping, for example:
  - `Shared - Historik`
  - `Local - Experiment`
- Add `Save locally`.
- Local prompt presets can be updated and deleted without password.
- Local prompts are included in main-page selection and Settings selection.

Why this slice:

- Users can experiment without affecting shared server prompts.

Verification:

- Save a local prompt and confirm it appears in the dropdown.
- Reload the page and confirm the local prompt remains.
- Confirm the local prompt is not returned by `/prompt-presets`.
- Delete the local prompt and confirm it disappears only from that browser.

Expected commit:

- `add local prompt presets`

## Task 8: Browser Ownership For Server Prompt Presets

Scope:

- Generate a browser owner id and keep it in `localStorage`.
- Send this owner id when creating or updating server prompt presets.
- Store `owner_id` on server prompt presets.
- Server prompts created before this change have no owner and require password for update/delete.
- Prompts created by the current browser can be updated/deleted by that browser without password.
- Other browsers need the shared unlock password to update/delete a server prompt.

Security note:

- Browser ownership is an ergonomic collaboration feature, not strong authentication. A technical user could spoof an owner id. The shared password remains the real protection.

Verification:

- Browser A creates a server prompt and can update/delete it without password.
- Browser B can view it but cannot update/delete without password.
- Browser B can update/delete it with the shared password.
- Existing ownerless server prompts require password for update/delete.

Expected commit:

- `protect shared prompt edits with browser ownership`

## Task 9: Require Password For Cross-Owner Shared Updates And Deletes

Scope:

- Introduce one general shared admin password setting, `ADMIN_PASSWORD`.
- Replace `LLM_UNLOCK_PASSWORD` as the preferred shared unlock setting.
- Do not keep backward compatibility for `LLM_UNLOCK_PASSWORD`; deployments should rename the setting to `ADMIN_PASSWORD`.
- Add password field or reuse the existing unlock state for protected prompt actions.
- Enforce permissions server-side for:
  - updating server prompt owned by another browser
  - deleting server prompt owned by another browser
  - updating/deleting ownerless server prompts
- Keep creating a new server prompt allowed without password.

Why this slice:

- It protects shared presets from accidental overwrites while preserving easy creation.

Verification:

- Attempt protected update/delete without password and confirm a 403/401-style error.
- Unlock and repeat; confirm it succeeds.
- Confirm creating a new server prompt still works without password.
- Note in docs that future public deployments may require the admin password for creating shared/server prompts too.

Expected commit:

- `require unlock for protected prompt changes`

## Task 10: Prompt Data Migration And Backward Compatibility

Scope:

- Normalize existing `data/prompt_presets.json` records into the new schema on load.
- Preserve old fields like `style_prompts` without requiring the UI to expose them.
- Decide whether to write back migrated records automatically or only when they are saved.
- Add tests for loading:
  - old prompt preset records
  - new prompt preset records
  - malformed prompt preset files
  - ownerless server prompt records

Why this slice:

- It reduces risk before future WP-specific prompt grouping.

Verification:

- Unit tests for preset normalization.
- Manual check that existing saved presets still appear in the dropdown.

Expected commit:

- `support prompt preset schema migration`

## Task 11: Prepare For Future WP/Avatar Grouping

Scope:

- Add optional fields to prompt preset records, but do not expose a full WP selector yet:
  - `wp_id`
  - maybe `collection_ids` later
- Default existing prompts to `WP1`.
- Keep UI behavior unchanged: show all prompts while there is only one active WP.
- Add comments or docs explaining how future WP filtering will use these fields.

Why this slice:

- It prepares for the future direction without prematurely building the WP selector.

Verification:

- Existing prompts still load and save.
- New records include the optional default `wp_id`.
- No UI regression.

Expected commit:

- `prepare prompt presets for avatar grouping`

## Task 12: Generalized Prompt Placeholders

Scope:

- Allow a prompt/WP to define additional placeholders beyond the initial built-ins.
- Keep the first UI simple; additional placeholders can initially be text fields in advanced settings.
- Store placeholder definitions with prompt or WP config, including:
  - key
  - label
  - default value
  - optional help text
- Continue rendering unknown placeholders literally if they have no definition.
- Prepare for future input types such as dropdowns or numbers, but do not build them unless needed.

Why this slice:

- It implements the next step after warning-only placeholder handling without introducing a full templating language too early.

Verification:

- Add a custom placeholder definition such as `{current_date}`.
- Confirm the value appears in rendered prompts.
- Confirm prompts without the placeholder are unaffected.

Expected commit:

- `support configurable prompt placeholders`

## Later Work: WP/Avatar Selector

Not part of the first implementation.

Future behavior:

- Add `Avatar` or `WP` selector before `Prompt`.
- The current collection/database selector will probably be replaced by the WP selector.
- Store server prompts under the relevant WP.
- Filter prompt presets by selected WP.
- Filter collections by selected WP.
- Allow multiple collections per WP later if needed.
- Define WP-specific defaults:
  - default prompt
  - default collection
  - length definitions
  - optional variables such as `{current_date}` for WP2
- Remove remaining Czech-history assumptions from generic app code.

## Open Questions

None at this stage.
