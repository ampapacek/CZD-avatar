const form = document.querySelector("#chatForm");
const question = document.querySelector("#question");
const style = document.querySelector("#style");
const length = document.querySelector("#length");
const customInstructions = document.querySelector("#customInstructions");
const model = document.querySelector("#model");
const customModelField = document.querySelector("#customModelField");
const customModel = document.querySelector("#customModel");
const llmBaseUrl = document.querySelector("#llmBaseUrl");
const llmApiKey = document.querySelector("#llmApiKey");
const llmUnlockPassword = document.querySelector("#llmUnlockPassword");
const unlockModelsButton = document.querySelector("#unlockModelsButton");
const retrieveOnly = document.querySelector("#retrieveOnly");
const retrievalBackend = document.querySelector("#retrievalBackend");
const msearchCollection = document.querySelector("#msearchCollection");
const msearchMode = document.querySelector("#msearchMode");
const msearchMinConfidence = document.querySelector("#msearchMinConfidence");
const promptPreset = document.querySelector("#promptPreset");
const savePromptButton = document.querySelector("#savePromptButton");
const resetPromptButton = document.querySelector("#resetPromptButton");
const deletePromptButton = document.querySelector("#deletePromptButton");
const llmPolicyNote = document.querySelector("#llmPolicyNote");
const systemPrompt = document.querySelector("#systemPrompt");
const stylePromptDescriptionLabel = document.querySelector("#stylePromptDescriptionLabel");
const stylePromptDescription = document.querySelector("#stylePromptDescription");
const lengthPromptDescriptionLabel = document.querySelector("#lengthPromptDescriptionLabel");
const lengthPromptDescription = document.querySelector("#lengthPromptDescription");
const userPromptTemplate = document.querySelector("#userPromptTemplate");
const topK = document.querySelector("#topK");
const topKValue = document.querySelector("#topKValue");
const denseWeight = document.querySelector("#denseWeight");
const denseWeightValue = document.querySelector("#denseWeightValue");
const bm25Weight = document.querySelector("#bm25Weight");
const bm25WeightValue = document.querySelector("#bm25WeightValue");
const minScore = document.querySelector("#minScore");
const minRelativeScore = document.querySelector("#minRelativeScore");
const embeddingModel = document.querySelector("#embeddingModel");
const submitButton = document.querySelector("#submitButton");
const randomQuestionButton = document.querySelector("#randomQuestionButton");
const statusEl = document.querySelector("#status");
const loadingIndicator = document.querySelector("#loadingIndicator");
const answerEl = document.querySelector("#answer");
const sourcesEl = document.querySelector("#sources");
const conversationButton = document.querySelector("#conversationButton");
const historyButton = document.querySelector("#historyButton");
const historyDialog = document.querySelector("#historyDialog");
const historyList = document.querySelector("#historyList");
const historyDetail = document.querySelector("#historyDetail");
const deleteHistoryItemButton = document.querySelector("#deleteHistoryItemButton");
const clearHistoryButton = document.querySelector("#clearHistoryButton");
const closeHistoryButton = document.querySelector("#closeHistoryButton");
const conversationDialog = document.querySelector("#conversationDialog");
const conversationList = document.querySelector("#conversationList");
const conversationMeta = document.querySelector("#conversationMeta");
const conversationMessages = document.querySelector("#conversationMessages");
const conversationSources = document.querySelector("#conversationSources");
const conversationForm = document.querySelector("#conversationForm");
const conversationQuestion = document.querySelector("#conversationQuestion");
const conversationSubmitButton = document.querySelector("#conversationSubmitButton");
const newConversationButton = document.querySelector("#newConversationButton");
const deleteConversationButton = document.querySelector("#deleteConversationButton");
const closeConversationButton = document.querySelector("#closeConversationButton");
const helpButton = document.querySelector("#helpButton");
const helpDialog = document.querySelector("#helpDialog");
const closeHelpButton = document.querySelector("#closeHelpButton");
const themeToggle = document.querySelector("#themeToggle");
const themeToggleLabel = document.querySelector("#themeToggleLabel");
const HISTORY_STORAGE_KEY = "czdemos4ai-history";
const CONVERSATION_STORAGE_KEY = "czdemos4ai-conversations";
const LLM_SETTINGS_STORAGE_KEY = "czdemos4ai-llm-settings";
const STYLE_LABELS = {
  laik: "laik",
  ucitel: "učitel",
  historik: "historik",
};
const LENGTH_LABELS = {
  short: "krátká",
  medium: "střední",
  long: "dlouhá",
};
const CUSTOM_MODEL_VALUE = "__custom__";

let selectedHistoryId = null;
let selectedConversationId = null;
let streamedAnswerText = "";
let currentAnswerSources = [];
let currentRetrievedChunks = [];
let appSettings = {};
let promptPresets = [];
let currentStylePrompts = {};
let currentLengthPrompts = {};
let llmModelsUnlocked = false;

async function loadSettings() {
  const response = await fetch("settings");
  const settings = await response.json();
  appSettings = settings;
  style.value = settings.default_style || "ucitel";
  length.value = settings.default_length || "medium";
  embeddingModel.value = settings.embedding_model || "";
  const savedLlmSettings = loadLlmSettings();
  llmBaseUrl.value = savedLlmSettings.llm_base_url || "";
  llmBaseUrl.placeholder = settings.llm_base_url || "https://api.openai.com/v1";
  llmApiKey.value = savedLlmSettings.llm_api_key || "";
  llmUnlockPassword.value = savedLlmSettings.llm_unlock_password || "";
  customModel.value = savedLlmSettings.llm_custom_model || "";
  refreshModelOptions(settings);
  if (llmUnlockPassword.value.trim()) {
    await verifyUnlockPassword({ silent: true });
  }
  populateMsearchCollections(settings.msearch_defaults?.collection_presets || [], settings.msearch_defaults?.collection);
  retrievalBackend.value = settings.retrieval_backend || "msearch";
  msearchMode.value = settings.msearch_defaults?.mode || "hybrid";
  msearchMinConfidence.value = settings.msearch_defaults?.min_confidence ?? "";
  topK.value = settings.msearch_defaults?.max_results ?? settings.top_k ?? 10;
  systemPrompt.value = settings.prompt_defaults?.system_prompt || "";
  userPromptTemplate.value = settings.prompt_defaults?.user_prompt_template || "";
  currentStylePrompts = { ...(settings.prompt_defaults?.style_prompts || {}) };
  currentLengthPrompts = { ...(settings.prompt_defaults?.length_prompts || {}) };
  updatePromptDescriptionEditors();
  topKValue.value = topK.value;
  denseWeight.value = settings.retrieval_defaults?.dense_weight ?? 0.7;
  bm25Weight.value = (1 - Number(denseWeight.value)).toFixed(2);
  minScore.value = settings.retrieval_defaults?.min_score ?? 0.2;
  minRelativeScore.value = settings.retrieval_defaults?.min_relative_score ?? 0.3;
  updateWeightLabels();
  updateRetrievalControls({ resetValues: false });
  applyTheme(localStorage.getItem("theme") || "light");
  renderHistory();
  renderConversationWorkspace();
  await loadPromptPresets();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitButton.disabled = true;
  statusEl.className = "status";
  statusEl.textContent = "Vyhledávám zdroje a generuji odpověď...";
  streamedAnswerText = "";
  currentAnswerSources = [];
  currentRetrievedChunks = [];
  renderAnswer("");
  sourcesEl.innerHTML = "";
  loadingIndicator.hidden = false;

  try {
    const payload = buildRequestPayload();

    if (retrieveOnly.checked) {
      const response = await fetch("retrieve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Request failed");
      }
      renderAnswer("Zobrazuji pouze nalezené dokumenty. Generování odpovědi bylo vypnuté.");
      statusEl.textContent = `Nalezeno ${data.retrieved_chunks.length} chunků.`;
      currentRetrievedChunks = data.retrieved_chunks;
      currentAnswerSources = chunksToSources(data.retrieved_chunks);
      renderSources(currentAnswerSources, currentRetrievedChunks, "");
      saveHistoryEntry({
        question: question.value,
        mode: "retrieve",
        answer: "Zobrazuji pouze nalezené dokumenty. Generování odpovědi bylo vypnuté.",
        sourceCount: data.retrieved_chunks.length,
        settings: payload,
        retrieved_chunks: data.retrieved_chunks,
        sources: chunksToSources(data.retrieved_chunks),
      });
    } else {
      const data = await streamChat(payload);
      streamedAnswerText = data.answer || streamedAnswerText;
      renderAnswer(streamedAnswerText);
      const modelLabel = formatModelUsageLabel(data.model, data.upstream_model);
      statusEl.textContent = modelLabel
        ? `Hotovo za ${data.response_time_seconds}s · ${modelLabel}`
        : `Hotovo za ${data.response_time_seconds}s`;
      currentAnswerSources = data.sources || [];
      currentRetrievedChunks = data.retrieved_chunks || [];
      renderSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
      saveHistoryEntry({
        question: question.value,
        mode: "chat",
        answer: data.answer || streamedAnswerText,
        sourceCount: data.retrieved_chunks?.length || 0,
        settings: payload,
        retrieved_chunks: data.retrieved_chunks || [],
        sources: data.sources || [],
        model_used: data.model || model.value,
        upstream_model: data.upstream_model || null,
        response_time_seconds: data.response_time_seconds,
      });
    }
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    loadingIndicator.hidden = true;
    submitButton.disabled = false;
  }
});

randomQuestionButton.addEventListener("click", async () => {
  randomQuestionButton.disabled = true;
  statusEl.className = "status";
  statusEl.textContent = "Vybírám náhodnou otázku...";
  try {
    const response = await fetch("questions/random");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Nepodařilo se vybrat náhodnou otázku.");
    }
    question.value = data.question || "";
    question.focus();
    statusEl.textContent = "Náhodná otázka je vložená. Spusť odpověď tlačítkem Odpovědět.";
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    randomQuestionButton.disabled = false;
  }
});

helpButton.addEventListener("click", () => {
  helpDialog.showModal();
});
closeHelpButton.addEventListener("click", () => {
  helpDialog.close();
});
helpDialog.addEventListener("click", (event) => {
  if (event.target === helpDialog) {
    helpDialog.close();
  }
});

historyButton.addEventListener("click", () => {
  renderHistory();
  historyDialog.showModal();
});
closeHistoryButton.addEventListener("click", () => {
  historyDialog.close();
});
historyDialog.addEventListener("click", (event) => {
  if (event.target === historyDialog) {
    historyDialog.close();
  }
});

conversationButton.addEventListener("click", () => {
  renderConversationWorkspace();
  conversationDialog.showModal();
});
closeConversationButton.addEventListener("click", () => {
  conversationDialog.close();
});
conversationDialog.addEventListener("click", (event) => {
  if (event.target === conversationDialog) {
    conversationDialog.close();
  }
});
newConversationButton.addEventListener("click", () => {
  createConversation();
  renderConversationWorkspace();
  conversationQuestion.focus();
});
deleteConversationButton.addEventListener("click", () => {
  deleteSelectedConversation();
});
conversationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await submitConversationTurn();
});
document.addEventListener("click", pulseSourceCardFromCitation);
question.addEventListener("keydown", (event) => maybeSubmitOnCommandEnter(event, form));
conversationQuestion.addEventListener("keydown", (event) => maybeSubmitOnCommandEnter(event, conversationForm));

clearHistoryButton.addEventListener("click", () => {
  localStorage.removeItem(HISTORY_STORAGE_KEY);
  selectedHistoryId = null;
  renderHistory();
});

deleteHistoryItemButton.addEventListener("click", () => {
  if (selectedHistoryId === null) {
    return;
  }
  const remainingHistory = getHistoryEntries().filter((entry) => entry.id !== selectedHistoryId);
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(remainingHistory));
  selectedHistoryId = remainingHistory[0]?.id ?? null;
  renderHistory();
});

topK.addEventListener("input", () => {
  topKValue.value = topK.value;
});

retrievalBackend.addEventListener("change", () => updateRetrievalControls({ resetValues: true }));
style.addEventListener("change", updatePromptDescriptionEditors);
length.addEventListener("change", updatePromptDescriptionEditors);
stylePromptDescription.addEventListener("input", () => {
  currentStylePrompts[style.value] = stylePromptDescription.value;
});
lengthPromptDescription.addEventListener("input", () => {
  currentLengthPrompts[length.value] = lengthPromptDescription.value;
});
  promptPreset.addEventListener("change", applySelectedPromptPreset);
savePromptButton.addEventListener("click", async () => {
  savePromptButton.disabled = true;
  try {
    await saveCurrentPromptPreset();
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    savePromptButton.disabled = false;
  }
});
resetPromptButton.addEventListener("click", resetPromptEditors);
deletePromptButton.addEventListener("click", async () => {
  deletePromptButton.disabled = true;
  try {
    await deleteSelectedPromptPreset();
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    deletePromptButton.disabled = promptPreset.value === "default";
  }
});

themeToggle.addEventListener("click", () => {
  const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
  localStorage.setItem("theme", nextTheme);
});
llmBaseUrl.addEventListener("input", persistLlmSettings);
llmApiKey.addEventListener("input", persistLlmSettings);
customModel.addEventListener("input", persistLlmSettings);
model.addEventListener("change", () => {
  updateCustomModelVisibility(llmModelsUnlocked);
  persistLlmSettings();
  if (model.value === CUSTOM_MODEL_VALUE) {
    customModel.focus();
  }
});
llmUnlockPassword.addEventListener("input", () => {
  persistLlmSettings();
  llmModelsUnlocked = false;
  refreshModelOptions(appSettings);
});
unlockModelsButton.addEventListener("click", () => verifyUnlockPassword());

function buildRequestPayload(overrides = {}) {
  return {
    question: question.value,
    style: style.value,
    length: length.value,
    custom_instructions: customInstructions.value,
    system_prompt: promptOverride(systemPrompt.value, appSettings.prompt_defaults?.system_prompt),
    user_prompt_template: promptOverride(userPromptTemplate.value, appSettings.prompt_defaults?.user_prompt_template),
    style_prompts: promptMapOverride(currentStylePrompts, appSettings.prompt_defaults?.style_prompts),
    length_prompts: promptMapOverride(currentLengthPrompts, appSettings.prompt_defaults?.length_prompts),
    conversation_history: [],
    model: selectedModelValue(),
    llm_base_url: nullableString(llmBaseUrl.value),
    llm_api_key: nullableString(llmApiKey.value),
    llm_unlock_password: llmModelsUnlocked ? nullableString(llmUnlockPassword.value) : null,
    top_k: Number(topK.value),
    retrieval_backend: retrievalBackend.value,
    msearch_collection: msearchCollection.value,
    msearch_mode: msearchMode.value,
    msearch_min_confidence: nullableNumber(msearchMinConfidence.value),
    dense_weight: Number(denseWeight.value),
    bm25_weight: Number(bm25Weight.value),
    min_score: nullableNumber(minScore.value),
    min_relative_score: nullableNumber(minRelativeScore.value),
    ...overrides,
  };
}

function loadLlmSettings() {
  try {
    const raw = JSON.parse(localStorage.getItem(LLM_SETTINGS_STORAGE_KEY) || "{}");
    return {
      llm_base_url: typeof raw.llm_base_url === "string" ? raw.llm_base_url : "",
      llm_api_key: typeof raw.llm_api_key === "string" ? raw.llm_api_key : "",
      llm_unlock_password: typeof raw.llm_unlock_password === "string" ? raw.llm_unlock_password : "",
      llm_custom_model: typeof raw.llm_custom_model === "string" ? raw.llm_custom_model : "",
    };
  } catch {
    return { llm_base_url: "", llm_api_key: "", llm_unlock_password: "", llm_custom_model: "" };
  }
}

function persistLlmSettings() {
  localStorage.setItem(
    LLM_SETTINGS_STORAGE_KEY,
    JSON.stringify({
      llm_base_url: llmBaseUrl.value.trim(),
      llm_api_key: llmApiKey.value,
      llm_unlock_password: llmUnlockPassword.value,
      llm_custom_model: customModel.value.trim(),
    }),
  );
}

async function verifyUnlockPassword({ silent = false } = {}) {
  const password = llmUnlockPassword.value.trim();
  if (!password) {
    llmModelsUnlocked = false;
    refreshModelOptions(appSettings);
    if (!silent) {
      statusEl.className = "status error";
      statusEl.textContent = "Zadej odemykací heslo.";
    }
    return false;
  }
  unlockModelsButton.disabled = true;
  try {
    const response = await fetch("unlock", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    const data = await response.json();
    if (!response.ok || !data.unlocked) {
      throw new Error("Odemykací heslo není správné.");
    }
    llmModelsUnlocked = true;
    persistLlmSettings();
    refreshModelOptions(appSettings);
    if (!silent) {
      statusEl.className = "status";
      statusEl.textContent = "Modely jsou odemčené.";
    }
    return true;
  } catch (error) {
    llmModelsUnlocked = false;
    refreshModelOptions(appSettings);
    if (!silent) {
      statusEl.className = "status error";
      statusEl.textContent = error.message;
    }
    return false;
  } finally {
    unlockModelsButton.disabled = false;
  }
}

async function streamChat(payload) {
  return streamChatWithHandlers(payload, {
    onSources(data) {
      currentRetrievedChunks = data.retrieved_chunks || [];
      currentAnswerSources = chunksToSources(currentRetrievedChunks);
      renderSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
      statusEl.textContent = `Nalezeno ${currentRetrievedChunks.length} chunků, odpovídám...`;
    },
    onToken(token) {
      streamedAnswerText += token;
      renderAnswer(streamedAnswerText);
    },
  });
}

async function streamChatWithHandlers(payload, handlers = {}) {
  const response = await fetch("chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await safeJson(response);
    throw new Error(data.detail || "Request failed");
  }
  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let donePayload = null;

  while (true) {
    const { value, done } = await reader.read();
    if (value) {
      buffer += decoder.decode(value, { stream: !done });
    }
    let separatorIndex = buffer.indexOf("\n\n");
    while (separatorIndex !== -1) {
      const rawEvent = buffer.slice(0, separatorIndex);
      buffer = buffer.slice(separatorIndex + 2);
      const event = parseSseEvent(rawEvent);
      if (event.event === "sources") {
        handlers.onSources?.(event.data);
      } else if (event.event === "token") {
        handlers.onToken?.(event.data.text || "", event.data);
      } else if (event.event === "done") {
        donePayload = event.data;
        handlers.onDone?.(donePayload);
      } else if (event.event === "error") {
        throw new Error(event.data.detail || "Streaming failed");
      }
      separatorIndex = buffer.indexOf("\n\n");
    }
    if (done) {
      break;
    }
  }

  if (!donePayload) {
    throw new Error("Streaming finished without a final response.");
  }
  return donePayload;
}

function parseSseEvent(rawEvent) {
  const lines = rawEvent.split(/\r?\n/);
  let eventName = "message";
  const dataLines = [];
  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }
  const dataText = dataLines.join("\n");
  let data = {};
  if (dataText) {
    try {
      data = JSON.parse(dataText);
    } catch {
      data = { text: dataText };
    }
  }
  return { event: eventName, data };
}

async function safeJson(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function populateModels(presets, currentModel, allowCustom = false) {
  const uniqueModels = Array.from(new Set(presets.filter(Boolean)));
  const options = uniqueModels.map((modelName) => `<option value="${escapeHtml(modelName)}">${escapeHtml(modelName)}</option>`);
  if (allowCustom) {
    options.push(`<option value="${escapeHtml(CUSTOM_MODEL_VALUE)}">Jiný model…</option>`);
  }
  model.innerHTML = options.join("");

  let selectedModel = currentModel;
  if (allowCustom && ((currentModel && !uniqueModels.includes(currentModel)) || (!currentModel && customModel.value.trim()))) {
    selectedModel = CUSTOM_MODEL_VALUE;
    customModel.value = currentModel || customModel.value.trim();
  } else if (!allowCustom && !uniqueModels.includes(currentModel)) {
    selectedModel = uniqueModels[0] || currentModel;
  }
  model.value = selectedModel || "";
  updateCustomModelVisibility(allowCustom);
}

function selectedModelValue() {
  return model.value === CUSTOM_MODEL_VALUE ? customModel.value.trim() : model.value;
}

function refreshModelOptions(settings = appSettings) {
  const publicModels = Array.isArray(settings.llm_policy?.public_models) ? settings.llm_policy.public_models.filter(Boolean) : [];
  const allModels = Array.isArray(settings.all_model_presets) ? settings.all_model_presets.filter(Boolean) : publicModels;
  const unlocked = llmModelsUnlocked;
  const allowedModels = unlocked ? allModels : publicModels;
  const currentModel = model.value === CUSTOM_MODEL_VALUE ? customModel.value.trim() || settings.llm_model : model.value || settings.llm_model;
  populateModels(allowedModels, currentModel, unlocked);
  updateLlmPolicyNote(settings.llm_policy, unlocked);
}

function updatePromptDescriptionEditors() {
  stylePromptDescriptionLabel.textContent = `Popis profilu ${STYLE_LABELS[style.value] || style.value} místo {style}`;
  lengthPromptDescriptionLabel.textContent = `Popis délky ${LENGTH_LABELS[length.value] || length.value} místo {length}`;
  stylePromptDescription.value = currentStylePrompts[style.value] || "";
  lengthPromptDescription.value = currentLengthPrompts[length.value] || "";
}

async function loadPromptPresets(selectedId = promptPreset.value || "default") {
  try {
    const response = await fetch("prompt-presets");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Prompt presets request failed");
    }
    promptPresets = Array.isArray(data) ? data : [];
  } catch (error) {
    promptPresets = [];
    console.warn("Could not load prompt presets", error);
  }
  renderPromptPresets(selectedId);
}

function renderPromptPresets(selectedId = promptPreset.value || "default") {
  promptPreset.innerHTML =
    `<option value="default">Výchozí prompt</option>` +
    promptPresets
      .map((preset) => `<option value="${escapeHtml(preset.id)}">${escapeHtml(preset.name)}</option>`)
      .join("");
  promptPreset.value = Array.from(promptPreset.options).some((option) => option.value === selectedId)
    ? selectedId
    : "default";
  deletePromptButton.disabled = promptPreset.value === "default";
}

function applySelectedPromptPreset() {
  if (promptPreset.value === "default") {
    resetPromptEditors();
    return;
  }
  const preset = promptPresets.find((item) => item.id === promptPreset.value);
  if (!preset) {
    renderPromptPresets("default");
    resetPromptEditors();
    return;
  }
  systemPrompt.value = preset.system_prompt || "";
  userPromptTemplate.value = preset.user_prompt_template || "";
  currentStylePrompts = { ...(appSettings.prompt_defaults?.style_prompts || {}), ...(preset.style_prompts || {}) };
  currentLengthPrompts = { ...(appSettings.prompt_defaults?.length_prompts || {}), ...(preset.length_prompts || {}) };
  updatePromptDescriptionEditors();
  deletePromptButton.disabled = false;
}

async function saveCurrentPromptPreset() {
  const currentPreset = promptPresets.find((item) => item.id === promptPreset.value);
  const proposedName = currentPreset?.name || "";
  const name = window.prompt("Název promptu", proposedName);
  if (!name || !name.trim()) {
    return;
  }
  const payload = {
    id: currentPreset?.id || null,
    name: name.trim(),
    system_prompt: systemPrompt.value,
    user_prompt_template: userPromptTemplate.value,
    style_prompts: currentStylePrompts,
    length_prompts: currentLengthPrompts,
  };
  const response = await fetch("prompt-presets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Prompt preset save failed");
  }
  await loadPromptPresets(data.id);
}

function resetPromptEditors() {
  systemPrompt.value = appSettings.prompt_defaults?.system_prompt || "";
  userPromptTemplate.value = appSettings.prompt_defaults?.user_prompt_template || "";
  currentStylePrompts = { ...(appSettings.prompt_defaults?.style_prompts || {}) };
  currentLengthPrompts = { ...(appSettings.prompt_defaults?.length_prompts || {}) };
  updatePromptDescriptionEditors();
  renderPromptPresets("default");
}

async function deleteSelectedPromptPreset() {
  if (promptPreset.value === "default") {
    return;
  }
  const response = await fetch(`prompt-presets/${encodeURIComponent(promptPreset.value)}`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 404) {
    const data = await safeJson(response);
    throw new Error(data.detail || "Prompt preset delete failed");
  }
  resetPromptEditors();
  await loadPromptPresets("default");
}

function populateMsearchCollections(presets, currentCollection) {
  const fallbackPresets = [
    {
      label: "WP1: histoedu v2026-02",
      collection_id: "64d6f521-5044-4b02-8658-380b639801af",
    },
    {
      label: "WP2: zaplavy v2025-11",
      collection_id: "35a4a85e-4d6e-42a3-a3ff-e1f151ffbd09",
    },
    {
      label: "WP3: law v2026-02",
      collection_id: "d4be44d5-689c-4bbe-a372-b959929cd511",
    },
    {
      label: "WP4: v2026-03",
      collection_id: "3429956e-8a21-4502-ad21-a41fddc5ef99",
    },
  ];
  const usablePresets = presets.length ? presets : fallbackPresets;
  msearchCollection.innerHTML = usablePresets
    .map((preset) => {
      const value = preset.collection_id || "";
      const label = preset.label || preset.collection_name || value;
      return `<option value="${escapeHtml(value)}">${escapeHtml(label)}</option>`;
    })
    .join("");
  msearchCollection.value = currentCollection || usablePresets[0]?.collection_id || "";
}

function updateRetrievalControls({ resetValues = false } = {}) {
  if (resetValues) {
    if (retrievalBackend.value === "msearch") {
      topK.value = appSettings.msearch_defaults?.max_results ?? 10;
      msearchMode.value = appSettings.msearch_defaults?.mode || "hybrid";
      msearchMinConfidence.value = appSettings.msearch_defaults?.min_confidence ?? "";
      if (appSettings.msearch_defaults?.collection) {
        msearchCollection.value = appSettings.msearch_defaults.collection;
      }
    } else {
      topK.value = appSettings.top_k ?? 10;
      denseWeight.value = appSettings.retrieval_defaults?.dense_weight ?? 0.7;
      bm25Weight.value = appSettings.retrieval_defaults?.bm25_weight ?? 0.3;
      minScore.value = appSettings.retrieval_defaults?.min_score ?? 0.2;
      minRelativeScore.value = appSettings.retrieval_defaults?.min_relative_score ?? 0.3;
      updateWeightLabels();
    }
    topKValue.value = topK.value;
  }
  for (const element of document.querySelectorAll(".msearch-control")) {
    element.classList.remove("is-hidden");
    element.hidden = false;
  }
  const embeddingField = embeddingModel.closest(".field");
  if (embeddingField) {
    embeddingField.classList.remove("is-hidden");
    embeddingField.hidden = false;
  }
}

function updateWeightLabels() {
  denseWeightValue.value = Number(denseWeight.value).toFixed(2);
  bm25WeightValue.value = Number(bm25Weight.value).toFixed(2);
}

denseWeight.addEventListener("input", () => {
  bm25Weight.value = (1 - Number(denseWeight.value)).toFixed(2);
  updateWeightLabels();
});

bm25Weight.addEventListener("input", () => {
  denseWeight.value = (1 - Number(bm25Weight.value)).toFixed(2);
  updateWeightLabels();
});

function applyTheme(theme) {
  document.body.dataset.theme = theme;
  themeToggle.title = theme === "dark" ? "Přepnout na světlý motiv" : "Přepnout na tmavý motiv";
  themeToggle.setAttribute("aria-label", themeToggle.title);
  if (themeToggleLabel) {
    themeToggleLabel.textContent = theme === "dark" ? "Světlý" : "Tmavý";
  }
}

function updateLlmPolicyNote(policy, unlocked = false) {
  if (!llmPolicyNote) {
    return;
  }
  const publicModels = Array.isArray(policy?.public_models) ? policy.public_models.filter(Boolean) : [];
  if (unlocked) {
    llmPolicyNote.textContent = "Odemčeno: v rozbalovacím seznamu jsou všechny dostupné modely a lze zadat i jiný model.";
    return;
  }
  if (publicModels.length > 0) {
    llmPolicyNote.textContent = `Bez odemykacího hesla jsou povolené jen tyto modely: ${publicModels.join(", ")}.`;
    return;
  }
  llmPolicyNote.textContent = "Dostupné jsou jen veřejné modely nastavené na serveru.";
}

function nullableNumber(value) {
  if (value === "") {
    return null;
  }
  return Number(value);
}

function nullableString(value) {
  const trimmed = String(value || "").trim();
  return trimmed ? trimmed : null;
}

function updateCustomModelVisibility(unlocked) {
  if (!customModelField) {
    return;
  }
  const showCustomField = unlocked && model.value === CUSTOM_MODEL_VALUE;
  customModelField.hidden = !showCustomField;
  customModelField.classList.toggle("is-hidden", !showCustomField);
}

function promptOverride(value, defaultValue) {
  const current = String(value || "").trim();
  const baseline = String(defaultValue || "").trim();
  if (!current || current === baseline) {
    return null;
  }
  return current;
}

function promptMapOverride(value, defaultValue) {
  const current = value || {};
  const baseline = defaultValue || {};
  const keys = Array.from(new Set([...Object.keys(current), ...Object.keys(baseline)]));
  for (const key of keys) {
    if ((current[key] || "") !== (baseline[key] || "")) {
      return current;
    }
  }
  return null;
}

function chunksToSources(chunks) {
  return chunks.map((chunk) => ({
    citation_id: chunk.citation_id,
    chunk_id: chunk.chunk_id,
    source_kind: chunk.metadata?.source_kind,
    title: chunk.metadata?.title,
    source_path: chunk.metadata?.source_path,
    source_path_display: chunk.metadata?.source_path_display,
    page_number: chunk.metadata?.page_number,
    url: chunk.metadata?.url,
    document_url: chunk.metadata?.document_url,
    source_url: chunk.metadata?.source_url,
    source_name: chunk.metadata?.source_name,
    score: chunk.score,
  }));
}

function renderSources(sources, chunks, answerText = streamedAnswerText) {
  renderSourceCards(sourcesEl, sources, chunks, question.value, extractCitationIds(answerText), "main-source");
}

function renderAnswer(text) {
  answerEl.innerHTML = renderMarkdown(text, currentAnswerSources, "main-source");
  updateUsedSourceHighlights(sourcesEl, extractCitationIds(text));
}

function renderSourceCards(container, sources, chunks, highlightQuery, usedCitationIds = new Set(), idPrefix = "source") {
  if (!sources.length) {
    container.textContent = "Žádné zdroje nebyly vráceny.";
    return;
  }
  const highlightTerms = extractHighlightTerms(highlightQuery);
  const chunkById = new Map((chunks || []).map((chunk) => [chunk.chunk_id, chunk]));
  container.innerHTML = sources
    .map((source) => {
      const chunk = chunkById.get(source.chunk_id);
      const title = escapeHtml(source.title || "Neznámý dokument");
      const path = escapeHtml(source.source_path_display || trimSourcePath(source.source_path || ""));
      const page = source.page_number ? ` · str. ${source.page_number}` : "";
      const documentUrl = source.document_url || source.url;
      const sourceUrl = source.source_url && source.source_url !== documentUrl ? source.source_url : null;
      const url = documentUrl ? ` · <a href="${escapeHtml(documentUrl)}" target="_blank" rel="noreferrer">Dokument</a>` : "";
      const metaUrl = sourceUrl ? ` · <a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">Zdroj</a>` : "";
      const fullText = chunk?.text || "";
      const excerptText = fullText.slice(0, 420);
      const excerpt = highlightText(excerptText, highlightTerms);
      const fullChunk = highlightText(fullText, highlightTerms);
      const canExpand = fullText.length > 420;
      const score = typeof source.score === "number" ? source.score.toFixed(2) : "";
      const dense = typeof chunk?.dense_score === "number" ? ` · emb ${chunk.dense_score.toFixed(2)}` : "";
      const bm25 = typeof chunk?.bm25_score === "number" ? ` · BM25 ${chunk.bm25_score.toFixed(2)}` : "";
      const citationId = source.citation_id || "";
      const usedClass = usedCitationIds.has(citationId) ? " used-source" : "";
      return `
        <article class="source${usedClass}" id="${escapeHtml(idPrefix)}-${escapeHtml(citationId)}" data-citation-id="${escapeHtml(citationId)}">
          <strong>[${escapeHtml(citationId)}] ${title}</strong>
          <p>${path}${page}${url}${metaUrl}</p>
          <p class="score">score ${score}${dense}${bm25}</p>
          <p class="excerpt">${excerpt}${excerptText.length >= 420 ? "..." : ""}</p>
          ${
            canExpand
              ? `<details class="chunk-details">
                  <summary>Zobrazit celý úryvek</summary>
                  <p class="full-chunk">${fullChunk}</p>
                </details>`
              : ""
          }
        </article>
      `;
    })
    .join("");
}

function updateUsedSourceHighlights(container, usedCitationIds) {
  for (const card of container.querySelectorAll(".source")) {
    const citationId = card.dataset.citationId || "";
    card.classList.toggle("used-source", usedCitationIds.has(citationId));
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function trimSourcePath(path) {
  return String(path).replace(/^data\/raw\//, "");
}

function extractHighlightTerms(text) {
  const stopwords = new Set([
    "a",
    "aby",
    "ale",
    "ano",
    "asi",
    "bez",
    "by",
    "byl",
    "byla",
    "byli",
    "bylo",
    "co",
    "do",
    "ho",
    "i",
    "jak",
    "jaký",
    "jaká",
    "jaké",
    "jakou",
    "jako",
    "je",
    "jeho",
    "její",
    "jejich",
    "jen",
    "jsme",
    "jsou",
    "jste",
    "k",
    "kde",
    "kdo",
    "když",
    "má",
    "mají",
    "mezi",
    "mi",
    "mně",
    "na",
    "nad",
    "ne",
    "nebo",
    "než",
    "o",
    "od",
    "on",
    "ona",
    "oni",
    "po",
    "pod",
    "pro",
    "proč",
    "proto",
    "před",
    "při",
    "se",
    "si",
    "s",
    "tak",
    "také",
    "tato",
    "ten",
    "tento",
    "této",
    "to",
    "toho",
    "tom",
    "u",
    "už",
    "v",
    "ve",
    "vy",
    "z",
    "za",
    "ze",
  ]);
  const tokens = String(text)
    .toLocaleLowerCase("cs-CZ")
    .match(/[\p{L}\p{N}][\p{L}\p{N}-]*/gu);
  if (!tokens) {
    return [];
  }
  return Array.from(new Set(tokens.filter((token) => token.length >= 4 && !stopwords.has(token)))).sort(
    (a, b) => b.length - a.length,
  );
}

function highlightText(text, terms) {
  if (!terms.length || !text) {
    return escapeHtml(text);
  }
  const pattern = new RegExp(`(${terms.map(escapeRegExp).join("|")})`, "giu");
  let lastIndex = 0;
  let result = "";

  for (const match of text.matchAll(pattern)) {
    const start = match.index ?? 0;
    const matchedText = match[0];
    result += escapeHtml(text.slice(lastIndex, start));
    result += `<mark class="source-highlight">${escapeHtml(matchedText)}</mark>`;
    lastIndex = start + matchedText.length;
  }

  result += escapeHtml(text.slice(lastIndex));
  return result;
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function pulseSourceCardFromCitation(event) {
  const trigger = event.target.closest(".footnote-ref a");
  if (!trigger) {
    return;
  }
  const citationId = trigger.dataset.citationId || "";
  if (!citationId) {
    return;
  }
  const scopeRoot =
    trigger.closest(".conversation-main") ||
    trigger.closest(".history-detail") ||
    trigger.closest(".answer-panel")?.closest(".workspace") ||
    document;
  const escapedCitationId = typeof CSS !== "undefined" && CSS.escape ? CSS.escape(citationId) : citationId;
  const sourceSelector = `.source[data-citation-id="${escapedCitationId}"]`;
  const sourceCard =
    (scopeRoot.classList?.contains("workspace")
      ? document.querySelector(`.sources-panel ${sourceSelector}`)
      : scopeRoot.querySelector(sourceSelector)) || null;
  if (!sourceCard) {
    return;
  }
  event.preventDefault();
  sourceCard.classList.remove("source-pulse");
  void sourceCard.offsetWidth;
  sourceCard.classList.add("source-pulse");
  sourceCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  window.setTimeout(() => {
    sourceCard.classList.remove("source-pulse");
  }, 1400);
}

function maybeSubmitOnCommandEnter(event, targetForm) {
  if (event.key !== "Enter" || !event.metaKey || event.shiftKey || event.altKey || event.ctrlKey) {
    return;
  }
  event.preventDefault();
  targetForm.requestSubmit();
}

function getConversationEntries() {
  try {
    return JSON.parse(localStorage.getItem(CONVERSATION_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function setConversationEntries(entries) {
  localStorage.setItem(CONVERSATION_STORAGE_KEY, JSON.stringify(entries));
}

function createConversation() {
  const conversations = getConversationEntries();
  const conversation = {
    id: Date.now(),
    title: "Nová konverzace",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: [],
  };
  conversations.unshift(conversation);
  setConversationEntries(conversations);
  selectedConversationId = conversation.id;
  return conversation;
}

function ensureSelectedConversation() {
  const conversations = getConversationEntries();
  if (!conversations.length) {
    return createConversation();
  }
  if (!conversations.some((entry) => entry.id === selectedConversationId)) {
    selectedConversationId = conversations[0].id;
  }
  return conversations.find((entry) => entry.id === selectedConversationId) || conversations[0];
}

function updateConversation(updatedConversation) {
  const conversations = getConversationEntries();
  const nextConversations = conversations.map((entry) =>
    entry.id === updatedConversation.id ? updatedConversation : entry,
  );
  nextConversations.sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
  setConversationEntries(nextConversations);
  selectedConversationId = updatedConversation.id;
}

function deleteSelectedConversation() {
  const conversations = getConversationEntries();
  if (!conversations.length || selectedConversationId === null) {
    return;
  }
  const remaining = conversations.filter((entry) => entry.id !== selectedConversationId);
  setConversationEntries(remaining);
  selectedConversationId = remaining[0]?.id ?? null;
  renderConversationWorkspace();
}

function renderConversationWorkspace() {
  const conversations = getConversationEntries();
  if (!conversations.length) {
    createConversation();
  }
  const conversation = ensureSelectedConversation();
  const refreshed = getConversationEntries();
  renderConversationList(refreshed);
  renderConversationDetail(conversation);
}

function renderConversationList(conversations) {
  if (!conversations.length) {
    conversationList.innerHTML = `<p class="history-empty">Zatím tu nejsou žádné konverzace.</p>`;
    deleteConversationButton.disabled = true;
    return;
  }
  deleteConversationButton.disabled = false;
  conversationList.innerHTML = conversations
    .map((entry) => {
      const lastAssistant = [...(entry.messages || [])].reverse().find((message) => message.role === "assistant");
      const summary = lastAssistant?.content ? shortenText(lastAssistant.content, 72) : "Bez odpovědi";
      return `
        <button class="history-item ${entry.id === selectedConversationId ? "active" : ""}" type="button" data-conversation-id="${entry.id}">
          <strong>${escapeHtml(entry.title || "Nová konverzace")}</strong>
          <span>${escapeHtml(summary)}</span>
          <span>${formatHistoryTime(entry.updatedAt || entry.createdAt)}</span>
        </button>
      `;
    })
    .join("");
  for (const item of conversationList.querySelectorAll(".history-item")) {
    item.addEventListener("click", () => {
      selectedConversationId = Number(item.dataset.conversationId);
      renderConversationWorkspace();
    });
  }
}

function renderConversationDetail(conversation) {
  const messages = conversation?.messages || [];
  const latestAssistant = [...messages].reverse().find((message) => message.role === "assistant");
  const latestSources =
    latestAssistant?.sources?.length ? latestAssistant.sources : chunksToSources(latestAssistant?.retrieved_chunks || []);
  const latestChunks = latestAssistant?.retrieved_chunks || [];

  conversationMeta.innerHTML = `
    <div>
      <h3>${escapeHtml(conversation?.title || "Nová konverzace")}</h3>
      <p class="conversation-meta-copy">
        ${messages.length ? `${messages.filter((message) => message.role === "user").length} dotazů v této konverzaci` : "Začni první otázkou."}
      </p>
    </div>
  `;

  if (!messages.length) {
    conversationMessages.innerHTML = `<p class="history-empty">Zatím tu nic není. Polož první otázku a pak na ni můžeš plynule navazovat.</p>`;
  } else {
    conversationMessages.innerHTML = messages
      .map((message) => renderConversationMessage(message))
      .join("");
    conversationMessages.scrollTop = conversationMessages.scrollHeight;
  }

  renderSourceCards(
    conversationSources,
    latestSources,
    latestChunks,
    latestAssistant?.question || conversationQuestion.value,
    extractCitationIds(latestAssistant?.content || ""),
    "conversation-source",
  );
}

function renderConversationMessage(message) {
  const roleLabel = message.role === "assistant" ? "Avatar" : "Ty";
  const messageClass = message.role === "assistant" ? "assistant" : "user";
  const body =
    message.role === "assistant"
      ? renderMarkdown(message.content || "", message.sources || [], "conversation-source")
      : `<p>${escapeHtml(message.content || "")}</p>`;
  const metaParts = [];
  if (message.role === "assistant" && message.model_used) {
    metaParts.push(escapeHtml(formatModelUsageLabel(message.model_used, message.upstream_model)));
  }
  if (message.role === "assistant" && message.response_time_seconds) {
    metaParts.push(`${escapeHtml(message.response_time_seconds)}s`);
  }
  return `
    <article class="conversation-message ${messageClass}">
      <div class="conversation-message-label">${roleLabel}</div>
      <div class="conversation-message-body">${body}</div>
      ${metaParts.length ? `<div class="conversation-message-meta">${metaParts.join(" · ")}</div>` : ""}
    </article>
  `;
}

async function submitConversationTurn() {
  const prompt = conversationQuestion.value.trim();
  if (!prompt) {
    return;
  }
  conversationSubmitButton.disabled = true;
  const conversation = ensureSelectedConversation();
  const userMessage = {
    role: "user",
    content: prompt,
    createdAt: new Date().toISOString(),
  };
  const workingConversation = {
    ...conversation,
    title: conversation.messages.length ? conversation.title : shortenText(prompt, 64),
    updatedAt: new Date().toISOString(),
    messages: [...conversation.messages, userMessage],
  };
  updateConversation(workingConversation);
  renderConversationWorkspace();
  conversationQuestion.value = "";

  let assistantText = "";
  let latestSources = [];
  let latestChunks = [];
  const payload = buildRequestPayload({
    question: prompt,
    conversation_history: conversation.messages.map((message) => ({
      role: message.role,
      content: message.content,
    })),
  });

  try {
    await streamChatWithHandlers(payload, {
      onSources(data) {
        latestChunks = data.retrieved_chunks || [];
        latestSources = chunksToSources(latestChunks);
        const liveConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id) || workingConversation;
        const messages = [...liveConversation.messages];
        const placeholderAssistant = messages[messages.length - 1];
        if (placeholderAssistant?.role === "assistant") {
          placeholderAssistant.content = assistantText;
          placeholderAssistant.sources = latestSources;
          placeholderAssistant.retrieved_chunks = latestChunks;
        } else {
          messages.push({
            role: "assistant",
            question: prompt,
            content: assistantText,
            sources: latestSources,
            retrieved_chunks: latestChunks,
            model_used: payload.model,
            upstream_model: null,
            response_time_seconds: null,
            createdAt: new Date().toISOString(),
          });
        }
        updateConversation({
          ...liveConversation,
          updatedAt: new Date().toISOString(),
          messages,
        });
        renderConversationWorkspace();
      },
      onToken(token) {
        assistantText += token;
        const liveConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id);
        if (!liveConversation) {
          return;
        }
        const messages = [...liveConversation.messages];
        const lastMessage = messages[messages.length - 1];
        if (lastMessage?.role === "assistant") {
          lastMessage.content = assistantText;
          lastMessage.sources = latestSources;
          lastMessage.retrieved_chunks = latestChunks;
        } else {
          messages.push({
            role: "assistant",
            question: prompt,
            content: assistantText,
            sources: latestSources,
            retrieved_chunks: latestChunks,
            model_used: payload.model,
            upstream_model: null,
            response_time_seconds: null,
            createdAt: new Date().toISOString(),
          });
        }
        updateConversation({ ...liveConversation, updatedAt: new Date().toISOString(), messages });
        renderConversationWorkspace();
      },
      onDone(data) {
        const liveConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id) || workingConversation;
        const messages = [...liveConversation.messages];
        const assistantMessage = {
          role: "assistant",
          question: prompt,
          content: data.answer || assistantText,
          sources: data.sources || latestSources,
          retrieved_chunks: data.retrieved_chunks || latestChunks,
          model_used: data.model || payload.model,
          upstream_model: data.upstream_model || null,
          response_time_seconds: data.response_time_seconds,
          createdAt: new Date().toISOString(),
        };
        if (messages[messages.length - 1]?.role === "assistant") {
          messages[messages.length - 1] = assistantMessage;
        } else {
          messages.push(assistantMessage);
        }
        updateConversation({ ...liveConversation, updatedAt: new Date().toISOString(), messages });
        renderConversationWorkspace();
      },
    });
  } catch (error) {
    const failedConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id) || workingConversation;
    updateConversation({
      ...failedConversation,
      updatedAt: new Date().toISOString(),
      messages: [
        ...failedConversation.messages,
        {
          role: "assistant",
          question: prompt,
          content: `Nepodařilo se dokončit odpověď: ${error.message}`,
          sources: [],
          retrieved_chunks: [],
          model_used: payload.model,
          response_time_seconds: null,
          createdAt: new Date().toISOString(),
        },
      ],
    });
    renderConversationWorkspace();
  } finally {
    conversationSubmitButton.disabled = false;
  }
}

function shortenText(text, limit = 80) {
  const compact = String(text || "").replace(/\s+/g, " ").trim();
  if (compact.length <= limit) {
    return compact;
  }
  return `${compact.slice(0, limit - 1).trimEnd()}…`;
}

function getHistoryEntries() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistoryEntry(entry) {
  const history = getHistoryEntries();
  history.unshift({
    id: Date.now(),
    question: entry.question,
    mode: entry.mode,
    answer: entry.answer,
    sourceCount: entry.sourceCount,
    settings: sanitizeHistorySettings(entry.settings || {}),
    retrieved_chunks: entry.retrieved_chunks || [],
    sources: entry.sources || [],
    model_used: entry.model_used || null,
    upstream_model: entry.upstream_model || null,
    response_time_seconds: entry.response_time_seconds ?? null,
    createdAt: new Date().toISOString(),
  });
  const trimmed = history.slice(0, 40);
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(trimmed));
  selectedHistoryId = trimmed[0]?.id ?? null;
  renderHistory();
}

function sanitizeHistorySettings(settings) {
  const sanitized = { ...settings };
  delete sanitized.llm_api_key;
  delete sanitized.llm_unlock_password;
  return sanitized;
}

function formatModelUsageLabel(requestedModel, upstreamModel) {
  const requested = String(requestedModel || "").trim();
  const upstream = String(upstreamModel || "").trim();
  if (requested && upstream && requested !== upstream) {
    return `${requested} · ${upstream}`;
  }
  return requested || upstream || "";
}

function renderHistory() {
  const history = getHistoryEntries();
  if (!history.length) {
    deleteHistoryItemButton.disabled = true;
    clearHistoryButton.disabled = true;
    historyList.innerHTML = `<p class="history-empty">Zatím tu nejsou žádné uložené dotazy.</p>`;
    historyDetail.innerHTML = `<p class="history-empty">Vyber položku z historie.</p>`;
    return;
  }

  deleteHistoryItemButton.disabled = false;
  clearHistoryButton.disabled = false;

  if (!history.some((entry) => entry.id === selectedHistoryId)) {
    selectedHistoryId = history[0].id;
  }

  historyList.innerHTML = history
    .map(
      (entry) => `
        <button class="history-item ${entry.id === selectedHistoryId ? "active" : ""}" type="button" data-history-id="${entry.id}">
          <strong>${escapeHtml(entry.question)}</strong>
          <span>${entry.mode === "retrieve" ? "Pouze zdroje" : "Odpověď"} · ${entry.sourceCount} zdrojů</span>
          <span>${formatHistoryTime(entry.createdAt)}</span>
        </button>
      `,
    )
    .join("");

  for (const item of historyList.querySelectorAll(".history-item")) {
    item.addEventListener("click", () => {
      selectedHistoryId = Number(item.dataset.historyId);
      renderHistory();
    });
  }

  const selectedEntry = history.find((entry) => entry.id === selectedHistoryId) || history[0];
  renderHistoryDetail(selectedEntry);
}

function renderHistoryDetail(entry) {
  const chunks = entry.retrieved_chunks || [];
  const sources = (entry.sources && entry.sources.length ? entry.sources : chunksToSources(chunks)) || [];
  const usedCitationIds = extractCitationIds(entry.answer || "");
  historyDetail.innerHTML = `
    <div class="history-detail-header">
      <div>
        <h3>${escapeHtml(entry.question)}</h3>
        <p>${entry.mode === "retrieve" ? "Pouze vyhledání zdrojů" : "Vygenerovaná odpověď"} · ${formatHistoryTime(entry.createdAt)}</p>
      </div>
      <button id="reuseHistoryButton" type="button">Načíst do formuláře</button>
    </div>
    <section class="history-block">
      <h4>Otázka</h4>
      <p class="history-question">${escapeHtml(entry.question)}</p>
    </section>
    <section class="history-block">
      <h4>Použitá nastavení</h4>
      <div class="settings-grid">
        ${renderSetting("Profil", entry.settings?.style)}
        ${renderSetting("Délka", entry.settings?.length)}
        ${renderSetting("Model", formatModelUsageLabel(entry.model_used || entry.settings?.model, entry.upstream_model))}
        ${renderSetting("LLM endpoint", entry.settings?.llm_base_url)}
        ${renderSetting("Pouze zdroje", entry.mode === "retrieve" ? "ano" : "ne")}
        ${renderSetting("Top-k", entry.settings?.top_k)}
        ${renderSetting("Váha embeddingů", entry.settings?.dense_weight)}
        ${renderSetting("Váha BM25", entry.settings?.bm25_weight)}
        ${renderSetting("Min. confidence mSearch", entry.settings?.msearch_min_confidence)}
        ${renderSetting("Min. skóre", entry.settings?.min_score)}
        ${renderSetting("Min. vůči nejlepšímu", entry.settings?.min_relative_score)}
        ${renderSetting("Doba odpovědi", entry.response_time_seconds ? `${entry.response_time_seconds}s` : null)}
        ${renderSetting("Vlastní instrukce", entry.settings?.custom_instructions || "žádné")}
      </div>
    </section>
    ${
      entry.answer
        ? `<section class="history-block">
            <h4>Odpověď</h4>
            <div class="history-answer">${renderMarkdown(entry.answer, sources, "history-source")}</div>
          </section>`
        : ""
    }
    <section class="history-block">
      <h4>Nalezené dokumenty</h4>
      <div id="historySources" class="sources history-sources"></div>
    </section>
  `;

  const reuseButton = historyDetail.querySelector("#reuseHistoryButton");
  reuseButton?.addEventListener("click", () => {
    applyHistoryEntryToForm(entry);
    historyDialog.close();
  });

  const historySources = historyDetail.querySelector("#historySources");
  renderSourceCards(historySources, sources, chunks, entry.question, usedCitationIds, "history-source");
}

function renderSetting(label, value) {
  const displayValue =
    label === "Profil"
      ? STYLE_LABELS[value] || value
      : label === "Délka"
        ? LENGTH_LABELS[value] || value
        : value;
  return `
    <div class="setting-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(displayValue ?? "—")}</strong>
    </div>
  `;
}

function applyHistoryEntryToForm(entry) {
  question.value = entry.question || "";
  style.value = entry.settings?.style || style.value;
  length.value = entry.settings?.length || length.value;
  customInstructions.value = entry.settings?.custom_instructions || "";
  systemPrompt.value = entry.settings?.system_prompt || systemPrompt.value;
  userPromptTemplate.value = entry.settings?.user_prompt_template || userPromptTemplate.value;
  currentStylePrompts = {
    ...(appSettings.prompt_defaults?.style_prompts || {}),
    ...(entry.settings?.style_prompts || {}),
  };
  currentLengthPrompts = {
    ...(appSettings.prompt_defaults?.length_prompts || {}),
    ...(entry.settings?.length_prompts || {}),
  };
  updatePromptDescriptionEditors();
  renderPromptPresets("default");
  const modelValue = entry.settings?.model || "";
  const unlocked = llmModelsUnlocked;
  if (modelValue && Array.from(model.options).some((option) => option.value === modelValue)) {
    model.value = modelValue;
  } else if (unlocked && modelValue) {
    customModel.value = modelValue;
    model.value = CUSTOM_MODEL_VALUE;
  } else if (model.options.length > 0) {
    model.value = model.options[0].value;
  }
  updateCustomModelVisibility(unlocked);
  llmBaseUrl.value = entry.settings?.llm_base_url || llmBaseUrl.value;
  persistLlmSettings();
  retrieveOnly.checked = entry.mode === "retrieve";
  retrievalBackend.value = entry.settings?.retrieval_backend || retrievalBackend.value;
  msearchCollection.value = entry.settings?.msearch_collection || msearchCollection.value;
  msearchMode.value = entry.settings?.msearch_mode || msearchMode.value;
  msearchMinConfidence.value = entry.settings?.msearch_min_confidence ?? "";
  topK.value = entry.settings?.top_k ?? topK.value;
  topKValue.value = topK.value;
  denseWeight.value = entry.settings?.dense_weight ?? denseWeight.value;
  bm25Weight.value = entry.settings?.bm25_weight ?? bm25Weight.value;
  minScore.value = entry.settings?.min_score ?? "";
  minRelativeScore.value = entry.settings?.min_relative_score ?? "";
  updateWeightLabels();
  updateRetrievalControls({ resetValues: false });
  question.focus();
}

function formatHistoryTime(timestamp) {
  try {
    return new Date(timestamp).toLocaleString("cs-CZ", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

function renderMarkdown(markdown, sources = [], sourceLinkPrefix = "source") {
  const citationMap = buildCitationMap(sources);
  const prepared = normalizeCitationMarkdown(markdown, citationMap);
  const citationOrderMap = buildCitationOrderMap(prepared.orderedCitationIds);
  const lines = prepared.markdown.split("\n");
  const html = [];
  const paragraph = [];
  const codeLines = [];
  let listType = null;
  let inCodeBlock = false;

  const flushParagraph = () => {
    if (!paragraph.length) {
      return;
    }
    html.push(
      `<p>${renderInlineMarkdown(paragraph.join("\n"), citationMap, prepared.usedCitationIds, citationOrderMap).replace(/\n/g, "<br>")}</p>`,
    );
    paragraph.length = 0;
  };

  const closeList = () => {
    if (!listType) {
      return;
    }
    html.push(listType === "ol" ? "</ol>" : "</ul>");
    listType = null;
  };

  for (const line of lines) {
    const fenceMatch = line.match(/^```([\w-]+)?\s*$/);
    if (fenceMatch) {
      flushParagraph();
      closeList();
      if (inCodeBlock) {
        html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
        codeLines.length = 0;
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      flushParagraph();
      closeList();
      const level = headingMatch[1].length;
      html.push(
        `<h${level}>${renderInlineMarkdown(headingMatch[2], citationMap, prepared.usedCitationIds, citationOrderMap)}</h${level}>`,
      );
      continue;
    }

    const blockquoteMatch = line.match(/^>\s?(.*)$/);
    if (blockquoteMatch) {
      flushParagraph();
      closeList();
      html.push(
        `<blockquote><p>${renderInlineMarkdown(blockquoteMatch[1], citationMap, prepared.usedCitationIds, citationOrderMap)}</p></blockquote>`,
      );
      continue;
    }

    const unorderedMatch = line.match(/^[-*+]\s+(.*)$/);
    if (unorderedMatch) {
      flushParagraph();
      if (listType !== "ul") {
        closeList();
        html.push("<ul>");
        listType = "ul";
      }
      html.push(`<li>${renderInlineMarkdown(unorderedMatch[1], citationMap, prepared.usedCitationIds, citationOrderMap)}</li>`);
      continue;
    }

    const orderedMatch = line.match(/^\d+\.\s+(.*)$/);
    if (orderedMatch) {
      flushParagraph();
      if (listType !== "ol") {
        closeList();
        html.push("<ol>");
        listType = "ol";
      }
      html.push(`<li>${renderInlineMarkdown(orderedMatch[1], citationMap, prepared.usedCitationIds, citationOrderMap)}</li>`);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      closeList();
      continue;
    }

    closeList();
    paragraph.push(line);
  }

  if (inCodeBlock) {
    html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
  } else {
    flushParagraph();
  }
  closeList();
  return `<div class="markdown-content">${html.join("")}${renderFootnotes(prepared.orderedCitationIds, citationMap, sourceLinkPrefix)}</div>`;
}

function renderInlineMarkdown(text, citationMap = new Map(), usedCitationIds = new Set(), citationOrderMap = new Map()) {
  const placeholders = [];
  const placeholderToken = (index) => `@@CODEXPH${index}@@`;
  let escaped = escapeHtml(text);
  escaped = escaped.replace(/\[\^([A-Z]{1,3}\d+)\]|\[([A-Z]{1,3}\d+)\]/g, (_, footnoteId, legacyId) => {
    const citationId = footnoteId || legacyId;
    if (!citationMap.has(citationId)) {
      return footnoteId ? `[^${citationId}]` : `[${citationId}]`;
    }
    usedCitationIds.add(citationId);
    const token = placeholderToken(placeholders.length);
    placeholders.push(
      `<sup class="footnote-ref"><a href="#fn-${citationId}" id="fnref-${citationId}" data-citation-id="${citationId}">${escapeHtml(String(citationOrderMap.get(citationId) || "?"))}</a></sup>`,
    );
    return token;
  });
  escaped = escaped.replace(/`([^`]+)`/g, (_, code) => {
    const token = placeholderToken(placeholders.length);
    placeholders.push(`<code>${code}</code>`);
    return token;
  });
  escaped = escaped.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, label, href) => {
    const token = placeholderToken(placeholders.length);
    placeholders.push(`<a href="${escapeHtml(href)}" target="_blank" rel="noreferrer">${label}</a>`);
    return token;
  });
  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  escaped = escaped.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  escaped = escaped.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  escaped = escaped.replace(/_([^_]+)_/g, "<em>$1</em>");
  return escaped.replace(/@@CODEXPH(\d+)@@/g, (_, index) => placeholders[Number(index)] || "");
}

function normalizeCitationMarkdown(markdown, citationMap) {
  const usedCitationIds = new Set();
  const normalized = String(markdown || "")
    .replace(/\r\n?/g, "\n")
    .replace(/^\[\^([A-Z]{1,3}\d+)\]:[^\n]*(?:\n(?!\[\^[A-Z]{1,3}\d+\]:).*)*/gm, "")
    .replace(/\n{2,}(?:#+\s*)?Použité zdroje:?\s*\n(?:[^\n]*\n?)*/i, "")
    .trim();
  const orderedCitationIds = Array.from(new Set(extractCitationIds(normalized))).filter((citationId) =>
    citationMap.has(citationId),
  );
  for (const citationId of orderedCitationIds) {
    usedCitationIds.add(citationId);
  }
  return { markdown: normalized, usedCitationIds, orderedCitationIds };
}

function buildCitationMap(sources) {
  return new Map((sources || []).filter((source) => source?.citation_id).map((source) => [source.citation_id, source]));
}

function buildCitationOrderMap(orderedCitationIds) {
  return new Map((orderedCitationIds || []).map((citationId, index) => [citationId, index + 1]));
}

function extractCitationIds(text) {
  const matches = String(text || "").match(/\[\^([A-Z]{1,3}\d+)\]|\[([A-Z]{1,3}\d+)\]/g) || [];
  const citationIds = new Set();
  for (const match of matches) {
    const citationId = match.replace(/[\[\]^]/g, "");
    if (citationId) {
      citationIds.add(citationId);
    }
  }
  return citationIds;
}

function renderFootnotes(orderedCitationIds, citationMap, sourceLinkPrefix = "source") {
  if (!orderedCitationIds.length) {
    return "";
  }
  const items = orderedCitationIds
    .map((citationId) => {
      const source = citationMap.get(citationId);
      if (!source) {
        return "";
      }
      const title = escapeHtml(source.title || citationId);
      const page = source.page_number ? `, str. ${escapeHtml(source.page_number)}` : "";
      const targetUrl = source.document_url || source.source_url || source.url;
      const titleHtml = targetUrl
        ? `<a href="${escapeHtml(targetUrl)}" target="_blank" rel="noreferrer">${title}</a>`
        : title;
      return `
        <li id="fn-${escapeHtml(citationId)}">
          <span class="footnote-label">[${escapeHtml(citationId)}]</span>
          ${titleHtml}${page}
        </li>
      `;
    })
    .filter(Boolean)
    .join("");
  if (!items) {
    return "";
  }
  return `
    <section class="footnotes">
      <h4>Poznámky a zdroje</h4>
      <ol>${items}</ol>
    </section>
  `;
}

loadSettings().catch((error) => {
  statusEl.className = "status error";
  statusEl.textContent = error.message;
});
