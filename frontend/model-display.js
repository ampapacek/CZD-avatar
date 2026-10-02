const MODEL_DISPLAY_OVERRIDES = new Map([
  ["openrouter/free", "OpenRouter Free"],
]);

// Compact only presentation noise. The raw model id remains the option value,
// so the compact and full-name selects always address the same model exactly.
export function shortenModelName(modelName) {
  const raw = String(modelName || "").trim();
  if (!raw) {
    return raw;
  }
  if (MODEL_DISPLAY_OVERRIDES.has(raw)) {
    return MODEL_DISPLAY_OVERRIDES.get(raw);
  }
  const label = raw
    // Host prefixes: "MAC2.", "LLM3.", "LLM1-A40." ...
    .replace(/^MAC\d*\./i, "")
    .replace(/^LLM[^.]*\./i, "")
    .replace(/^mlx-com{1,2}unity--/i, "")
    .replace(/^(?:unsloth|mlx-community|openai|meta-llama|google|anthropic|mistralai)\//i, "")
    .replace(/(?:-GGUF.*|-MLX.*|:UD-Q8_K_XL|:latest|-int4)$/i, "")
    .trim();
  return label || raw;
}

// Colliding compact labels are ambiguous in a select. In that case both
// affected models deliberately keep their full raw names.
export function modelDisplayLabels(modelNames) {
  const rawNames = (modelNames || []).map((name) => String(name || ""));
  const compact = rawNames.map(shortenModelName);
  const counts = new Map();
  for (const label of compact) {
    counts.set(label, (counts.get(label) || 0) + 1);
  }
  return rawNames.map((raw, index) => counts.get(compact[index]) > 1 ? raw : compact[index]);
}
