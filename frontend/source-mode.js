// "Bez zdrojů": answering from the bare model, without retrieval.
//
// The mode is chosen in the collection selector, so it is stored wherever the
// collection already is (conversation snapshots, history entries) under this
// sentinel value. Each prompt declares which mode it belongs to with
// `uses_sources`; a prompt without the flag predates the mode and uses sources.

export const NO_SOURCES_COLLECTION = "__no_sources__";
export const NO_SOURCES_LABEL = "Bez zdrojů";

export function collectionUsesSources(collection) {
  return collection !== NO_SOURCES_COLLECTION;
}

export function promptUsesSources(preset) {
  return preset?.uses_sources !== false;
}

export function promptsForMode(presets, useSources) {
  return (presets || []).filter((preset) => promptUsesSources(preset) === useSources);
}

/**
 * The prompt to switch to after entering a mode: the one last used in it if it
 * still fits, then the WP default if it fits, then the first prompt of the mode.
 * `null` when the WP has no prompt for the mode.
 */
export function pickPromptForMode(presets, useSources, { rememberedId = "", defaultId = "" } = {}) {
  const candidates = promptsForMode(presets, useSources);
  const byId = (id) => (id ? candidates.find((preset) => preset.id === id) : null);
  return (byId(rememberedId) || byId(defaultId) || candidates[0] || null)?.id ?? null;
}

/**
 * The system and user prompt a chat request carries. With sources, a text that
 * equals the built-in default is sent as null and the server fills it in.
 * Without sources the text is sent as written, because an empty system prompt
 * there means "no system message", not "use the default".
 */
export function requestPromptTexts({ systemPrompt, userPromptTemplate, defaults = {}, useSources = true }) {
  if (!useSources) {
    return {
      system_prompt: String(systemPrompt ?? ""),
      user_prompt_template: String(userPromptTemplate ?? ""),
    };
  }
  return {
    system_prompt: defaultAsNull(systemPrompt, defaults.system_prompt),
    user_prompt_template: defaultAsNull(userPromptTemplate, defaults.user_prompt_template),
  };
}

function defaultAsNull(value, defaultValue) {
  const current = String(value || "").trim();
  const baseline = String(defaultValue || "").trim();
  if (!current || current === baseline) {
    return null;
  }
  return current;
}

/**
 * Editor texts after the "Používá zdroje" checkbox flips. A text still equal to
 * the other mode's starting text (or empty) is swapped for this mode's starting
 * text; anything the user wrote is left alone.
 */
export function promptTextsForModeSwitch({ systemPrompt, userPromptTemplate, useSources, defaults = {} }) {
  const from = useSources ? defaults.noSources : defaults.sources;
  const to = useSources ? defaults.sources : defaults.noSources;
  const swap = (value, fromText, toText) => {
    const current = String(value ?? "").trim();
    return !current || current === String(fromText || "").trim() ? String(toText || "") : String(value ?? "");
  };
  return {
    systemPrompt: swap(systemPrompt, from?.system_prompt, to?.system_prompt),
    userPromptTemplate: swap(userPromptTemplate, from?.user_prompt_template, to?.user_prompt_template),
  };
}
