// A presentation filter only: discovery, metadata and server access policy keep
// the complete catalogue. Unknown naming schemes remain available via Show all.
function modelGroup(id) {
  if (/:/.test(id)) return null; // Batch/free routes are in the full view.
  const snapshot = id.match(/-(\d{4}-\d{2}-\d{2}|\d{8}|\d{4})$/)?.[1] || "";
  const name = snapshot ? id.slice(0, -snapshot.length - 1) : id;
  const preview = /-(preview|exp)$/.test(name);
  const base = name.replace(/-(preview|exp)$/, "");
  let match;
  let group;
  let version;
  if ((match = base.match(/^openai\/gpt-(\d+(?:\.\d+)*)(?:o)?(?:-(mini|nano|sol|luna|astra|terra))?$/))) {
    group = `gpt:${match[2] || "base"}`;
    version = match[1];
  } else if ((match = base.match(/^openai\/gpt-oss-(\d+)b$/))) {
    group = `gpt-oss:${match[1]}b`;
    version = "0";
  } else if ((match = base.match(/^google\/gemini-(\d+(?:\.\d+)*)-(pro|flash|flash-lite)$/))) {
    group = `gemini:${match[2]}`;
    version = match[1];
  } else if ((match = base.match(/^anthropic\/claude-(sonnet|haiku)-(\d+(?:\.\d+)*)$/))
    || (match = base.match(/^anthropic\/claude-(\d+(?:\.\d+)*)-(sonnet|haiku)$/))) {
    const modern = /^(sonnet|haiku)$/.test(match[1]);
    group = `claude:${modern ? match[1] : match[2]}`;
    version = modern ? match[2] : match[1];
  } else if ((match = base.match(/^deepseek\/deepseek-(?:chat-)?v(\d+(?:\.\d+)*)(?:-(pro|flash))?$/))) {
    // The generic V-series and newer Pro route occupy the general model slot.
    group = `deepseek:${match[2] || "pro"}`;
    version = match[1];
  } else if ((match = base.match(/^deepseek\/deepseek-r(\d+(?:\.\d+)*)$/))) {
    group = "deepseek:reasoning";
    version = match[1];
  } else {
    return null;
  }
  return { group, rank: [...version.split(".").map(Number), 0, 0].slice(0, 3), preview, snapshot };
}

function isNewer(candidate, existing) {
  for (let i = 0; i < candidate.rank.length; i += 1) {
    if (candidate.rank[i] !== existing.rank[i]) return candidate.rank[i] > existing.rank[i];
  }
  // On the same version prefer stable, then the unpinned route over a snapshot.
  if (candidate.preview !== existing.preview) return !candidate.preview;
  if (Boolean(candidate.snapshot) !== Boolean(existing.snapshot)) return !candidate.snapshot;
  return candidate.snapshot > existing.snapshot;
}

export function curatedOpenRouterModels(models = []) {
  const newest = new Map();
  for (const id of models) {
    const info = modelGroup(id);
    if (!info) continue;
    const previous = newest.get(info.group);
    if (!previous || isNewer(info, previous.info)) newest.set(info.group, { id, info });
  }
  const selected = new Set([...newest.values()].map(({ id }) => id));
  return models.filter((id) => selected.has(id));
}

export function modelSelectorView(provider, { unlocked = false, showAll = false, currentModel = "" } = {}) {
  const catalogue = [...new Set(provider?.model_presets || [])];
  const publicModels = (provider?.public_models || []).filter((id) => catalogue.includes(id));
  const allowed = unlocked ? catalogue : publicModels;
  const filterAvailable = provider?.id === "openrouter" && unlocked;
  if (!filterAvailable || showAll) return { models: allowed, filterAvailable, selectedOutsideFilter: false };
  const curated = curatedOpenRouterModels(allowed);
  // Keep public router(s) and the current choice, without granting extra access.
  const retained = new Set([...curated, ...publicModels]);
  const selectedOutsideFilter = allowed.includes(currentModel) && !retained.has(currentModel);
  if (allowed.includes(currentModel)) retained.add(currentModel);
  return { models: allowed.filter((id) => retained.has(id)), filterAvailable, selectedOutsideFilter };
}
