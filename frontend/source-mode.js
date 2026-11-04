// "Bez zdrojů": answering without retrieval, the same as top_k=0.
//
// The mode is chosen in the collection selector, so it is stored wherever the
// collection already is (conversation snapshots, history entries) under this
// sentinel value. A prompt without {retrieved_snippets} has no use for sources,
// so the UI holds the selector on this value while that prompt is active.

export const NO_SOURCES_COLLECTION = "__no_sources__";
export const NO_SOURCES_LABEL = "Bez zdrojů";

const RETRIEVED_SNIPPETS_PATTERN = /\{retrieved_snippets(?:![rsa])?(?::[^{}]*)?\}/;

export function collectionUsesSources(collection) {
  return collection !== NO_SOURCES_COLLECTION;
}

/** Whether a request retrieves at all: "Bez zdrojů" and top_k=0 are the same. */
export function retrievalEnabled({ collection, topK }) {
  return collectionUsesSources(collection) && Number(topK) > 0;
}

/**
 * Whether a prompt puts the sources anywhere. An empty text stands for the
 * server default, which `defaults` carries (`prompt_defaults` from /settings).
 */
export function promptUsesSources({ systemPrompt, userPromptTemplate }, defaults = {}) {
  const texts = [
    String(systemPrompt ?? "").trim() || String(defaults.system_prompt ?? ""),
    String(userPromptTemplate ?? "").trim() || String(defaults.user_prompt_template ?? ""),
  ];
  return texts.some((text) => RETRIEVED_SNIPPETS_PATTERN.test(text));
}
