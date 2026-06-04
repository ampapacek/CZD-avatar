const form = document.querySelector("#chatForm");
const question = document.querySelector("#question");
const placeholderControls = document.querySelector("#placeholderControls");
const llmProvider = document.querySelector("#llmProvider");
const model = document.querySelector("#model");
const customModelField = document.querySelector("#customModelField");
const customModel = document.querySelector("#customModel");
const llmBaseUrl = document.querySelector("#llmBaseUrl");
const llmApiKey = document.querySelector("#llmApiKey");
const llmUnlockPassword = document.querySelector("#llmUnlockPassword");
const unlockModelsButton = document.querySelector("#unlockModelsButton");
const toggleUnlockPasswordButton = document.querySelector("#toggleUnlockPasswordButton");
const unlockModelsStatus = document.querySelector("#unlockModelsStatus");
const refreshModelsButton = document.querySelector("#refreshModelsButton");
const modelRefreshStatus = document.querySelector("#modelRefreshStatus");
const contextWindowTokens = document.querySelector("#contextWindowTokens");
const outputBudgetShort = document.querySelector("#outputBudgetShort");
const outputBudgetMedium = document.querySelector("#outputBudgetMedium");
const outputBudgetLong = document.querySelector("#outputBudgetLong");
const minPromptChunks = document.querySelector("#minPromptChunks");
const tokenBudgetSafetyMargin = document.querySelector("#tokenBudgetSafetyMargin");
const conversationSummaryTriggerTokens = document.querySelector("#conversationSummaryTriggerTokens");
const providerApiKeyList = document.querySelector("#providerApiKeyList");
const customProviderName = document.querySelector("#customProviderName");
const customProviderBaseUrl = document.querySelector("#customProviderBaseUrl");
const customProviderApiKey = document.querySelector("#customProviderApiKey");
const saveCustomProviderApiKeyButton = document.querySelector("#saveCustomProviderApiKeyButton");
const clearCustomProviderApiKeyButton = document.querySelector("#clearCustomProviderApiKeyButton");
const customProviderDefaultModel = document.querySelector("#customProviderDefaultModel");
const customProviderModels = document.querySelector("#customProviderModels");
const retrieveOnly = document.querySelector("#retrieveOnly");
const retrievalBackend = document.querySelector("#retrievalBackend");
const msearchCollection = document.querySelector("#msearchCollection");
const msearchMode = document.querySelector("#msearchMode");
const msearchMinConfidence = document.querySelector("#msearchMinConfidence");
const wpSelect = document.querySelector("#wpSelect");
const activePromptPreset = document.querySelector("#activePromptPreset");
const promptPreset = document.querySelector("#promptPreset");
const newPromptButton = document.querySelector("#newPromptButton");
const savePromptAsButton = document.querySelector("#savePromptAsButton");
const sharePromptOnServer = document.querySelector("#sharePromptOnServer");
const promptShareNote = document.querySelector("#promptShareNote");
const updatePromptButton = document.querySelector("#updatePromptButton");
const deletePromptButton = document.querySelector("#deletePromptButton");
const llmPolicyNote = document.querySelector("#llmPolicyNote");
const systemPrompt = document.querySelector("#systemPrompt");
const userPromptTemplate = document.querySelector("#userPromptTemplate");
const promptTemplateWarning = document.querySelector("#promptTemplateWarning");
const globalPlaceholderDefsList = document.querySelector("#globalPlaceholderDefsList");
const newGlobalPlaceholderButton = document.querySelector("#newGlobalPlaceholderButton");
const inlinePlaceholderDefsList = document.querySelector("#inlinePlaceholderDefsList");
const newInlinePlaceholderButton = document.querySelector("#newInlinePlaceholderButton");
const placeholderDefDialog = document.querySelector("#placeholderDefDialog");
const placeholderDefForm = document.querySelector("#placeholderDefForm");
const placeholderDefTitle = document.querySelector("#placeholderDefTitle");
const placeholderDefScopeNote = document.querySelector("#placeholderDefScopeNote");
const closePlaceholderDefButton = document.querySelector("#closePlaceholderDefButton");
const placeholderDefName = document.querySelector("#placeholderDefName");
const placeholderDefLabel = document.querySelector("#placeholderDefLabel");
const placeholderDefHelp = document.querySelector("#placeholderDefHelp");
const placeholderDefKind = document.querySelector("#placeholderDefKind");
const placeholderDefDefaultTextField = document.querySelector("#placeholderDefDefaultTextField");
const placeholderDefDefaultText = document.querySelector("#placeholderDefDefaultText");
const placeholderDefDefaultSelectField = document.querySelector("#placeholderDefDefaultSelectField");
const placeholderDefDefaultSelect = document.querySelector("#placeholderDefDefaultSelect");
const placeholderDefOptionsBlock = document.querySelector("#placeholderDefOptionsBlock");
const placeholderDefOptionsList = document.querySelector("#placeholderDefOptionsList");
const addPlaceholderOptionButton = document.querySelector("#addPlaceholderOptionButton");
const placeholderDefError = document.querySelector("#placeholderDefError");
const placeholderDefActions = document.querySelector("#placeholderDefActions");
const topK = document.querySelector("#topK");
const topKValue = document.querySelector("#topKValue");
const denseWeight = document.querySelector("#denseWeight");
const denseWeightValue = document.querySelector("#denseWeightValue");
const bm25Weight = document.querySelector("#bm25Weight");
const bm25WeightValue = document.querySelector("#bm25WeightValue");
const rerankField = document.querySelector("#rerankField");
const rerankWeight = document.querySelector("#rerankWeight");
const rerankWeightValue = document.querySelector("#rerankWeightValue");
const rerankCandidatesField = document.querySelector("#rerankCandidatesField");
const rerankCandidates = document.querySelector("#rerankCandidates");
const rerankNote = document.querySelector("#rerankNote");
let rerankAvailable = false;
const minScore = document.querySelector("#minScore");
const minRelativeScore = document.querySelector("#minRelativeScore");
const embeddingModel = document.querySelector("#embeddingModel");
const submitButton = document.querySelector("#submitButton");
const randomQuestionButton = document.querySelector("#randomQuestionButton");
const statusEl = document.querySelector("#status");
const loadingIndicator = document.querySelector("#loadingIndicator");
const rerankProgressEl = document.querySelector("#rerankProgress");
const rerankProgressFill = document.querySelector("#rerankProgressFill");
const rerankProgressLabel = document.querySelector("#rerankProgressLabel");
const answerEl = document.querySelector("#answer");
const sourcesEl = document.querySelector("#sources");
const baselineSourcesEl = document.querySelector("#baselineSources");
const baselineColumnEl = document.querySelector("#baselineColumn");
const rerankedColumnTitleEl = document.querySelector("#rerankedColumnTitle");
const toggleBaselineBtn = document.querySelector("#toggleBaseline");
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
const settingsButton = document.querySelector("#settingsButton");
const settingsDialog = document.querySelector("#settingsDialog");
const closeSettingsButton = document.querySelector("#closeSettingsButton");
const helpButton = document.querySelector("#helpButton");
const helpDialog = document.querySelector("#helpDialog");
const closeHelpButton = document.querySelector("#closeHelpButton");
const themeToggle = document.querySelector("#themeToggle");
const themeToggleLabel = document.querySelector("#themeToggleLabel");
// Bumped for Task 14c: history entries now store a generic placeholder
// `selections` map instead of the old `style`/`length`/`custom_instructions`
// fields. Stale entries in the old key are simply dropped (no migration).
const HISTORY_STORAGE_KEY = "czdemos4ai-history-v2";
const CONVERSATION_STORAGE_KEY = "czdemos4ai-conversations";
const LLM_SETTINGS_STORAGE_KEY = "czdemos4ai-llm-settings";
const TOKEN_BUDGET_STORAGE_KEY = "czdemos4ai-token-budget";
const LOCAL_PROMPT_PRESETS_STORAGE_KEY = "czdemos4ai-local-prompt-presets";
// Browser-local global placeholder defs (name -> def). Private to this browser,
// no password. In resolution they sit between inline (on the selected prompt) and
// the shared server overlay: inline -> browser-local -> shared overlay -> code floor.
const LOCAL_PLACEHOLDER_DEFS_STORAGE_KEY = "czdemos4ai-local-placeholder-defs";
const BROWSER_OWNER_ID_STORAGE_KEY = "czdemos4ai-browser-owner-id";
const CUSTOM_PROVIDER_ID = "custom";
const DEFAULT_CUSTOM_PROVIDER_LABEL = "Custom provider";
const LEGACY_DEFAULT_PROMPT_PRESET_ID = "default";
const BUILTIN_PROMPT_PREFIX = "builtin-";
const LOCAL_PROMPT_PREFIX = "local-";
// System placeholders are filled by the server and never warned about; the two
// parameter placeholders shipped in the code floor (length, custom_instructions)
// are also "known" so they do not trigger the unknown-variable warning.
const KNOWN_PROMPT_VARIABLES = new Set([
  "question",
  "context",
  "current_date",
  "length",
  "custom_instructions",
]);
const CUSTOM_MODEL_VALUE = "__custom__";

let selectedHistoryId = null;
let selectedConversationId = null;
let streamedAnswerText = "";
let currentAnswerSources = [];
let currentRetrievedChunks = [];
let currentOmittedChunks = [];
let currentBaselineChunks = [];
let baselineVisible = false;
let currentBudgetWarnings = [];
let currentTokenBudget = null;
let currentConversationSummary = "";
let appSettings = {};
let promptPresets = [];
let localPromptPresets = [];
let activePromptPresetId = "";
let activeWpId = "";
// Resolved parameter placeholder defs for the active prompt (name -> def) and the
// current control values (name -> value). Both are rebuilt on every prompt switch.
let activePlaceholderDefs = {};
let placeholderSelections = {};
// Browser-local global placeholder defs (name -> def), loaded from localStorage.
let localPlaceholderDefs = {};
let llmModelsUnlocked = false;
let llmSettingsState = {
  selected_provider: "",
  provider_settings: {},
  admin_password: "",
};

function normalizeProviderId(providerId) {
  return String(providerId || "").trim().toLowerCase();
}

function getWpConfigs() {
  return Array.isArray(appSettings.wps) ? appSettings.wps : [];
}

function getWpConfig(wpId) {
  return getWpConfigs().find((wp) => wp.id === wpId) || null;
}

function resolveWpId(wpId) {
  const configs = getWpConfigs();
  if (configs.some((wp) => wp.id === wpId)) {
    return wpId;
  }
  if (appSettings.default_wp && configs.some((wp) => wp.id === appSettings.default_wp)) {
    return appSettings.default_wp;
  }
  return configs[0]?.id || "";
}

function wpDefaultCollectionMsearchId(wp) {
  if (!wp) {
    return "";
  }
  const collections = wp.collections || [];
  const preferred = collections.find((collection) => collection.id === wp.default_collection_id);
  return (preferred || collections[0])?.msearch_collection_id || "";
}

function populateWpSelect() {
  wpSelect.innerHTML = getWpConfigs()
    .map((wp) => `<option value="${escapeHtml(wp.id)}">${escapeHtml(wp.label || wp.id)}</option>`)
    .join("");
  wpSelect.value = activeWpId;
}

// Switch the active work package: pick its default collection and prompt, which
// in turn loads the WP's length definitions and re-renders the WP-filtered
// prompt options. Pass explicit ids when restoring a saved conversation.
function selectWp(wpId, { promptId, collectionId } = {}) {
  activeWpId = resolveWpId(wpId);
  wpSelect.value = activeWpId;
  const wp = getWpConfig(activeWpId);
  populateMsearchCollections(collectionId || wpDefaultCollectionMsearchId(wp));
  const targetPrompt = promptId && promptPresetExists(promptId)
    ? promptId
    : defaultPromptPresetId(activeWpId);
  applyPromptPresetById(targetPrompt);
}

const AI_UFAL_HOST = "ai.ufal.mff.cuni.cz";
const WP2_MSEARCH_COLLECTION = "35a4a85e-4d6e-42a3-a3ff-e1f151ffbd09";

function isAiUfalBaseUrl(baseUrl) {
  try {
    const parsed = new URL(String(baseUrl || "").trim());
    return parsed.protocol === "https:" && parsed.hostname === AI_UFAL_HOST;
  } catch {
    return false;
  }
}

function currentProviderBaseUrl() {
  return selectedProviderBaseUrl();
}

async function loadSettings() {
  const response = await fetch("settings");
  const settings = await response.json();
  logLlmModelRefresh("page-load", settings);
  appSettings = settings;
  localPlaceholderDefs = loadLocalPlaceholderDefs();
  embeddingModel.value = settings.embedding_model || "";
  llmSettingsState = loadLlmSettings();
  const providers = getLlmProviders(settings);
  const selectedProvider =
    normalizeProviderId(llmSettingsState.selected_provider || settings.llm_provider || providers[0]?.id || "");
  populateProviderOptions(providers, selectedProvider);
  populateCustomProviderFields();
  renderProviderApiKeyFields();
  loadProviderValues(selectedProvider, { preferStored: true });
  llmUnlockPassword.value = llmSettingsState.admin_password || "";
  populateTokenBudgetFields(settings);
  if (llmUnlockPassword.value.trim()) {
    await verifyUnlockPassword({ silent: true });
  }
  refreshModelOptions(settings);
  activeWpId = resolveWpId(settings.default_wp);
  populateWpSelect();
  populateMsearchCollections(wpDefaultCollectionMsearchId(getWpConfig(activeWpId)));
  retrievalBackend.value = settings.retrieval_backend || "msearch";
  msearchMode.value = settings.msearch_defaults?.mode || "hybrid";
  msearchMinConfidence.value = settings.msearch_defaults?.min_confidence ?? "";
  topK.value = settings.msearch_defaults?.max_results ?? settings.top_k ?? 10;
  systemPrompt.value = settings.prompt_defaults?.system_prompt || "";
  userPromptTemplate.value = settings.prompt_defaults?.user_prompt_template || "";
  updatePromptTemplateWarning();
  topKValue.value = topK.value;
  denseWeight.value = settings.retrieval_defaults?.dense_weight ?? 0.7;
  bm25Weight.value = (1 - Number(denseWeight.value)).toFixed(2);
  minScore.value = settings.retrieval_defaults?.min_score ?? 0.2;
  minRelativeScore.value = settings.retrieval_defaults?.min_relative_score ?? 0.3;
  rerankAvailable = settings.retrieval_defaults?.rerank_available ?? false;
  rerankWeight.value = settings.retrieval_defaults?.rerank_weight ?? 0;
  rerankCandidates.value = settings.retrieval_defaults?.rerank_candidates ?? 40;
  updateWeightLabels();
  updateRerankControls();
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
  currentOmittedChunks = [];
  currentBaselineChunks = [];
  baselineVisible = false;
  currentBudgetWarnings = [];
  currentTokenBudget = null;
  currentConversationSummary = "";
  renderAnswer("");
  sourcesEl.innerHTML = "";
  baselineSourcesEl.innerHTML = "";
  renderBaselineComparison();
  stopRerankCountdown();
  loadingIndicator.hidden = false;

  try {
    if (retrieveOnly.checked) {
      const payload = buildRetrievePayload();
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
      currentBaselineChunks = data.baseline_chunks || [];
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
      const payload = buildRequestPayload();
      const data = await chatRequest(payload, {
        onPreliminarySources(prelimData) {
          // First-stage hits shown while the cross-encoder runs; replaced by the
          // reranked order once the "sources" event arrives.
          currentRetrievedChunks = prelimData.retrieved_chunks || [];
          currentBaselineChunks = [];
          currentAnswerSources = prelimData.sources || chunksToSources(currentRetrievedChunks);
          renderSources(currentAnswerSources, currentRetrievedChunks, "");
          statusEl.textContent = `Nalezeno ${currentRetrievedChunks.length} dokumentů, přeřazuji (re-ranking)...`;
        },
        onRerankProgress(progress) {
          statusEl.textContent = "Přeřazuji (re-ranking)...";
          onRerankProgressUpdate(progress);
        },
        onSources(sourceData) {
          stopRerankCountdown();
          currentRetrievedChunks = sourceData.retrieved_chunks || [];
          currentBaselineChunks = sourceData.baseline_chunks || [];
          currentOmittedChunks = sourceData.omitted_chunks || [];
          currentBudgetWarnings = sourceData.chunk_budget_warnings || [];
          currentTokenBudget = sourceData.token_budget || null;
          currentConversationSummary = sourceData.conversation_summary || "";
          currentAnswerSources = sourceData.sources || chunksToSources(currentRetrievedChunks);
          renderSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
          statusEl.textContent = `Nalezeno ${currentRetrievedChunks.length} chunků, odpovídám...`;
        },
        onToken(token) {
          streamedAnswerText += token;
          renderAnswer(streamedAnswerText);
        },
        onDone(doneData) {
          const modelLabel = formatModelUsageLabel(doneData.model, doneData.upstream_model);
          statusEl.textContent = formatTimingLabel(doneData, modelLabel);
          currentAnswerSources = doneData.sources || currentAnswerSources;
          currentRetrievedChunks = doneData.retrieved_chunks || currentRetrievedChunks;
          currentBaselineChunks = doneData.baseline_chunks || currentBaselineChunks;
          currentOmittedChunks = doneData.omitted_chunks || currentOmittedChunks;
          currentBudgetWarnings = doneData.chunk_budget_warnings || currentBudgetWarnings;
          currentTokenBudget = doneData.token_budget || currentTokenBudget;
          currentConversationSummary = doneData.conversation_summary || currentConversationSummary;
          renderSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
        },
      });
      streamedAnswerText = data.answer || streamedAnswerText;
      renderAnswer(streamedAnswerText);
      currentAnswerSources = data.sources || currentAnswerSources;
      currentRetrievedChunks = data.retrieved_chunks || currentRetrievedChunks;
      currentBaselineChunks = data.baseline_chunks || currentBaselineChunks;
      currentOmittedChunks = data.omitted_chunks || currentOmittedChunks;
      currentBudgetWarnings = data.chunk_budget_warnings || currentBudgetWarnings;
      currentTokenBudget = data.token_budget || currentTokenBudget;
      currentConversationSummary = data.conversation_summary || currentConversationSummary;
      renderSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
      saveHistoryEntry({
        question: question.value,
        mode: "chat",
        answer: data.answer || streamedAnswerText,
        sourceCount: data.retrieved_chunks?.length || 0,
        settings: payload,
        retrieved_chunks: data.retrieved_chunks || [],
        omitted_chunks: data.omitted_chunks || [],
        token_budget: data.token_budget || null,
        chunk_budget_warnings: data.chunk_budget_warnings || [],
        conversation_summary: data.conversation_summary || null,
        sources: data.sources || [],
        model_used: data.model || model.value,
        upstream_model: data.upstream_model || null,
        response_time_seconds: data.response_time_seconds,
        rerank_time_seconds: data.rerank_time_seconds ?? null,
        generation_time_seconds: data.generation_time_seconds ?? null,
      });
    }
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    stopRerankCountdown();
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

settingsButton.addEventListener("click", () => {
  renderProviderApiKeyFields();
  populateCustomProviderFields();
  renderGlobalPlaceholderDefs();
  renderInlinePlaceholderDefs();
  settingsDialog.showModal();
});
closeSettingsButton.addEventListener("click", () => {
  settingsDialog.close();
});
settingsDialog.addEventListener("click", (event) => {
  if (event.target === settingsDialog) {
    settingsDialog.close();
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
// Editing the prompt text can change which {tokens} are used, so re-render the
// main-page controls (resetting values to the resolved defaults) and refresh the
// unknown-variable warning.
systemPrompt.addEventListener("input", () => {
  renderPlaceholderControls();
  updatePromptTemplateWarning();
});
userPromptTemplate.addEventListener("input", () => {
  renderPlaceholderControls();
  updatePromptTemplateWarning();
});
wpSelect.addEventListener("change", () => selectWp(wpSelect.value));
activePromptPreset.addEventListener("change", () => applyPromptPresetById(activePromptPreset.value));
promptPreset.addEventListener("change", applySelectedPromptPreset);
sharePromptOnServer.addEventListener("change", updatePromptShareNote);
updatePromptShareNote();
savePromptAsButton.addEventListener("click", async () => {
  savePromptAsButton.disabled = true;
  try {
    if (sharePromptOnServer.checked) {
      await saveCurrentPromptPreset({ mode: "create" });
    } else {
      await saveCurrentPromptPresetLocally({ mode: "create" });
    }
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    savePromptAsButton.disabled = false;
  }
});
updatePromptButton.addEventListener("click", async () => {
  if (!isEditablePromptPreset(promptPreset.value)) {
    return;
  }
  updatePromptButton.disabled = true;
  try {
    if (isLocalPromptPreset(promptPreset.value)) {
      await saveCurrentPromptPresetLocally({ mode: "update" });
    } else {
      await saveCurrentPromptPreset({ mode: "update" });
    }
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    updatePromptButton.disabled = !isEditablePromptPreset(promptPreset.value);
  }
});
newPromptButton.addEventListener("click", createBlankPromptDraft);
deletePromptButton.addEventListener("click", async () => {
  deletePromptButton.disabled = true;
  try {
    await deleteSelectedPromptPreset();
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    deletePromptButton.disabled = !isEditablePromptPreset(promptPreset.value);
  }
});

themeToggle.addEventListener("click", () => {
  const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
  applyTheme(nextTheme);
  localStorage.setItem("theme", nextTheme);
});
llmProvider.addEventListener("change", () => {
  const providerId = normalizeProviderId(llmProvider.value);
  loadProviderValues(providerId, { preferStored: true });
  refreshModelOptions(appSettings);
  populateMsearchCollections(msearchCollection.value);
  updateRetrievalControls({ resetValues: false });
  persistLlmSettings();
});
llmBaseUrl.addEventListener("input", () => {
  persistLlmSettings();
  populateMsearchCollections(msearchCollection.value);
});
llmApiKey.addEventListener("input", () => {
  persistLlmSettings();
  refreshModelOptions(appSettings);
});
providerApiKeyList.addEventListener("click", (event) => {
  const toggleButton = event.target.closest("[data-toggle-secret]");
  if (toggleButton) {
    toggleSecretField(toggleButton);
    return;
  }
  const clearButton = event.target.closest("[data-clear-provider-api-key]");
  if (clearButton) {
    clearProviderApiKey(clearButton.dataset.clearProviderApiKey);
    renderProviderApiKeyFields();
    refreshModelOptions(appSettings);
    return;
  }
  const button = event.target.closest("[data-save-provider-api-key]");
  if (!button) {
    return;
  }
  const providerId = button.dataset.saveProviderApiKey;
  const input = providerApiKeyList.querySelector(`[data-provider-api-key="${cssEscape(providerId)}"]`);
  if (!input) {
    return;
  }
  if (!input.value.trim()) {
    clearProviderApiKey(providerId);
    renderProviderApiKeyFields();
    refreshModelOptions(appSettings);
    return;
  }
  saveProviderApiKey(providerId, input.value);
  input.placeholder = "Klíč je uložený v tomto prohlížeči";
  renderProviderApiKeyFields();
  refreshModelOptions(appSettings);
});
refreshModelsButton.addEventListener("click", refreshProviderModels);
customModel.addEventListener("input", persistLlmSettings);
model.addEventListener("change", () => {
  updateCustomModelVisibility(customModelAllowed());
  persistLlmSettings();
  if (model.value === CUSTOM_MODEL_VALUE) {
    customModel.focus();
  }
});
llmUnlockPassword.addEventListener("input", () => {
  llmModelsUnlocked = false;
  setUnlockStatus("");
  persistLlmSettings();
  refreshModelOptions(appSettings);
});
customProviderName.addEventListener("input", () => {
  persistLlmSettings();
  populateProviderOptions(getLlmProviders(appSettings), llmProvider.value);
});
customProviderBaseUrl.addEventListener("input", () => {
  persistLlmSettings();
  loadProviderValues(llmProvider.value, { preferStored: true });
  populateMsearchCollections(msearchCollection.value);
});
saveCustomProviderApiKeyButton.addEventListener("click", () => {
  if (!customProviderApiKey.value.trim()) {
    clearProviderApiKey(CUSTOM_PROVIDER_ID);
    populateCustomProviderFields();
    refreshModelOptions(appSettings);
    return;
  }
  saveProviderApiKey(CUSTOM_PROVIDER_ID, customProviderApiKey.value);
  customProviderApiKey.placeholder = "Klíč je uložený v tomto prohlížeči";
  refreshModelOptions(appSettings);
});
clearCustomProviderApiKeyButton.addEventListener("click", () => {
  clearProviderApiKey(CUSTOM_PROVIDER_ID);
  populateCustomProviderFields();
  refreshModelOptions(appSettings);
});
customProviderDefaultModel.addEventListener("input", () => {
  persistLlmSettings();
  refreshModelOptions(appSettings);
});
customProviderModels.addEventListener("input", () => {
  persistLlmSettings();
  refreshModelOptions(appSettings);
});
[contextWindowTokens, outputBudgetShort, outputBudgetMedium, outputBudgetLong, minPromptChunks, tokenBudgetSafetyMargin, conversationSummaryTriggerTokens].forEach((input) => {
  input.addEventListener("input", persistTokenBudgetSettings);
});
unlockModelsButton.addEventListener("click", () => verifyUnlockPassword());
toggleUnlockPasswordButton.addEventListener("click", () => {
  toggleSecretField(toggleUnlockPasswordButton);
});

document.querySelectorAll("[data-toggle-secret]").forEach((button) => {
  button.addEventListener("click", (event) => {
    if (event.currentTarget === toggleUnlockPasswordButton) {
      return;
    }
    toggleSecretField(event.currentTarget);
  });
});

function buildRequestPayload(overrides = {}) {
  const activePrompt = activePromptPresetMetadata();
  return {
    question: question.value,
    wp_id: activeWpId,
    prompt_preset_id: activePrompt.id,
    prompt_preset_name: activePrompt.name,
    // Generic placeholder values + the FULLY RESOLVED effective defs (inline ->
    // browser-local global -> shared overlay) so the server substitutes exactly
    // what the user configured, including browser-local globals it cannot see.
    selections: { ...placeholderSelections },
    placeholder_defs: effectivePlaceholderDefsForRequest(),
    system_prompt: promptOverride(systemPrompt.value, appSettings.prompt_defaults?.system_prompt),
    user_prompt_template: promptOverride(userPromptTemplate.value, appSettings.prompt_defaults?.user_prompt_template),
    conversation_history: [],
    ...currentTokenBudgetSettings(),
    model: selectedModelValue(),
    llm_provider: llmProvider.value,
    llm_base_url: nullableString(selectedProviderBaseUrl()),
    llm_api_key: nullableString(selectedProviderApiKey()),
    admin_password: llmModelsUnlocked ? nullableString(llmUnlockPassword.value) : null,
    top_k: Number(topK.value),
    retrieval_backend: retrievalBackend.value,
    msearch_collection: msearchCollection.value,
    msearch_mode: msearchMode.value,
    msearch_min_confidence: nullableNumber(msearchMinConfidence.value),
    dense_weight: Number(denseWeight.value),
    bm25_weight: Number(bm25Weight.value),
    min_score: nullableNumber(minScore.value),
    min_relative_score: nullableNumber(minRelativeScore.value),
    rerank_weight: Number(rerankWeight.value),
    rerank_enabled: rerankAvailable && Number(rerankWeight.value) > 0,
    rerank_candidates: nullableNumber(rerankCandidates.value),
    ...overrides,
  };
}

function buildRetrievePayload(overrides = {}) {
  const activePrompt = activePromptPresetMetadata();
  return {
    question: question.value,
    wp_id: activeWpId,
    prompt_preset_id: activePrompt.id,
    prompt_preset_name: activePrompt.name,
    top_k: Number(topK.value),
    retrieval_backend: retrievalBackend.value,
    msearch_collection: msearchCollection.value,
    msearch_mode: msearchMode.value,
    msearch_min_confidence: nullableNumber(msearchMinConfidence.value),
    dense_weight: Number(denseWeight.value),
    bm25_weight: Number(bm25Weight.value),
    min_score: nullableNumber(minScore.value),
    min_relative_score: nullableNumber(minRelativeScore.value),
    rerank_weight: Number(rerankWeight.value),
    rerank_enabled: rerankAvailable && Number(rerankWeight.value) > 0,
    rerank_candidates: nullableNumber(rerankCandidates.value),
    ...overrides,
  };
}

function loadLlmSettings() {
  try {
    const raw = JSON.parse(localStorage.getItem(LLM_SETTINGS_STORAGE_KEY) || "{}");
    if (raw.provider_settings && typeof raw.provider_settings === "object") {
      return {
        selected_provider: typeof raw.selected_provider === "string" ? normalizeProviderId(raw.selected_provider) : "",
        provider_settings: raw.provider_settings,
        admin_password: typeof raw.admin_password === "string" ? raw.admin_password : "",
      };
    }
    const legacyProvider = typeof raw.llm_provider === "string" ? normalizeProviderId(raw.llm_provider) : "";
    const legacySettings = legacyProvider
      ? {
          [legacyProvider]: {
            base_url: typeof raw.llm_base_url === "string" ? raw.llm_base_url : "",
            api_key: typeof raw.llm_api_key === "string" ? raw.llm_api_key : "",
            custom_model: typeof raw.llm_custom_model === "string" ? raw.llm_custom_model : "",
          },
        }
      : {};
    return {
      selected_provider: legacyProvider,
      provider_settings: legacySettings,
      admin_password: typeof raw.admin_password === "string" ? raw.admin_password : "",
    };
  } catch {
    return { selected_provider: "", provider_settings: {}, admin_password: "" };
  }
}

function customProviderSettings() {
  return (llmSettingsState.provider_settings || {})[CUSTOM_PROVIDER_ID] || {};
}

function customProviderConfigured() {
  const settings = customProviderSettings();
  return Boolean(
    String(settings.label || "").trim()
      || String(settings.base_url || "").trim()
      || String(settings.default_model || "").trim()
      || String(settings.models || "").trim()
      || String(settings.custom_model || "").trim()
      || selectedProviderApiKey(CUSTOM_PROVIDER_ID),
  );
}

function customProviderConfig() {
  const settings = customProviderSettings();
  const defaultModel = String(settings.default_model || settings.custom_model || "").trim();
  const configuredModels = splitModelList(settings.models || "");
  const modelPresets = Array.from(new Set([defaultModel, settings.custom_model, ...configuredModels].filter(Boolean)));
  return {
    id: CUSTOM_PROVIDER_ID,
    label: String(settings.label || "").trim() || DEFAULT_CUSTOM_PROVIDER_LABEL,
    base_url: String(settings.base_url || "").trim(),
    default_model: defaultModel,
    model_presets: modelPresets,
    public_models: [],
    supports_streaming: true,
    api_key_label: "API key",
  };
}

function getLlmProviders(settings = appSettings) {
  const configuredProviders = Array.isArray(settings.llm_providers) ? settings.llm_providers : [];
  const providers = configuredProviders.filter((provider) => provider?.id !== CUSTOM_PROVIDER_ID);
  return customProviderConfigured() ? [...providers, customProviderConfig()] : providers;
}

function configuredEnvProviders(settings = appSettings) {
  return (Array.isArray(settings.llm_providers) ? settings.llm_providers : []).filter(
    (provider) => provider?.id !== CUSTOM_PROVIDER_ID,
  );
}

function renderProviderApiKeyFields() {
  const providers = configuredEnvProviders(appSettings);
  providerApiKeyList.innerHTML = providers
    .map((provider) => {
      const savedKey = selectedProviderApiKey(provider.id);
      const placeholder = savedKey ? "Klíč je uložený v tomto prohlížeči" : provider.api_key_label || "API key";
      const providerLabel = provider.label || provider.id || "vybraného poskytovatele";
      const publicModels = providerPublicModels(provider, appSettings);
      const policyNote =
        publicModels.length > 0
          ? `Bez odemykacího hesla jsou pro ${providerLabel} dostupné aktuálně načtené veřejné modely: ${publicModels.join(", ")}.`
          : `Pro ${providerLabel} zadej API klíč v Nastavení, nebo nastav veřejné modely v .env.`;
      return `
        <label class="field provider-key-row">
          <span>${escapeHtml(provider.label || provider.id)}</span>
          <div class="inline-actions">
            <div class="secret-field">
              <input type="password" data-provider-api-key="${escapeHtml(provider.id)}" value="${escapeHtml(savedKey)}" placeholder="${escapeHtml(placeholder)}" autocomplete="off" />
              <button class="secret-toggle" type="button" data-toggle-secret aria-label="Zobrazit API klíč" title="Zobrazit API klíč">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                  <circle cx="12" cy="12" r="3"></circle>
                </svg>
              </button>
            </div>
            <button class="secondary" type="button" data-save-provider-api-key="${escapeHtml(provider.id)}">Uložit klíč</button>
            <button class="secondary danger-lite" type="button" data-clear-provider-api-key="${escapeHtml(provider.id)}">Smazat klíč</button>
          </div>
          <span class="field-note">${escapeHtml(policyNote)}</span>
        </label>
      `;
    })
    .join("");
}

function populateCustomProviderFields() {
  const settings = customProviderSettings();
  customProviderName.value = String(settings.label || "").trim();
  customProviderBaseUrl.value = String(settings.base_url || "").trim();
  customProviderDefaultModel.value = String(settings.default_model || "").trim();
  customProviderModels.value = String(settings.models || "").trim();
  customProviderApiKey.value = selectedProviderApiKey(CUSTOM_PROVIDER_ID);
  customProviderApiKey.placeholder = selectedProviderApiKey(CUSTOM_PROVIDER_ID)
    ? "Klíč je uložený v tomto prohlížeči"
    : "Uložit klíč pro vlastního providera";
}

function persistLlmSettings() {
  const providerId = normalizeProviderId(llmProvider.value);
  const providerSettings = { ...(llmSettingsState.provider_settings || {}) };
  const selectedSettings = { ...(providerSettings[providerId] || {}) };
  selectedSettings.custom_model = customModel.value.trim();
  providerSettings[providerId] = selectedSettings;
  providerSettings[CUSTOM_PROVIDER_ID] = {
    ...(providerSettings[CUSTOM_PROVIDER_ID] || {}),
    label: customProviderName.value.trim(),
    base_url: customProviderBaseUrl.value.trim(),
    default_model: customProviderDefaultModel.value.trim(),
    models: customProviderModels.value.trim(),
  };
  if (providerId === CUSTOM_PROVIDER_ID) {
    providerSettings[CUSTOM_PROVIDER_ID] = {
      ...providerSettings[CUSTOM_PROVIDER_ID],
      custom_model: customModel.value.trim(),
    };
  }
  llmSettingsState = {
    selected_provider: providerId,
    provider_settings: providerSettings,
    admin_password: llmUnlockPassword.value,
  };
  localStorage.setItem(
    LLM_SETTINGS_STORAGE_KEY,
    JSON.stringify({
      selected_provider: llmSettingsState.selected_provider,
      provider_settings: llmSettingsState.provider_settings,
      admin_password: llmSettingsState.admin_password,
    }),
  );
}

function saveProviderApiKey(providerId, apiKey) {
  const normalizedProviderId = normalizeProviderId(providerId);
  const nextApiKey = String(apiKey || "").trim();
  if (!normalizedProviderId || !nextApiKey) {
    return;
  }
  const providerSettings = { ...(llmSettingsState.provider_settings || {}) };
  providerSettings[normalizedProviderId] = {
    ...(providerSettings[normalizedProviderId] || {}),
    api_key: nextApiKey,
    api_key_saved: true,
  };
  llmSettingsState = {
    ...llmSettingsState,
    provider_settings: providerSettings,
  };
  localStorage.setItem(
    LLM_SETTINGS_STORAGE_KEY,
    JSON.stringify({
      selected_provider: llmSettingsState.selected_provider,
      provider_settings: llmSettingsState.provider_settings,
      admin_password: llmSettingsState.admin_password,
    }),
  );
}

function clearProviderApiKey(providerId) {
  const normalizedProviderId = normalizeProviderId(providerId);
  if (!normalizedProviderId) {
    return;
  }
  const providerSettings = { ...(llmSettingsState.provider_settings || {}) };
  providerSettings[normalizedProviderId] = {
    ...(providerSettings[normalizedProviderId] || {}),
  };
  delete providerSettings[normalizedProviderId].api_key;
  delete providerSettings[normalizedProviderId].api_key_saved;
  llmSettingsState = {
    ...llmSettingsState,
    provider_settings: providerSettings,
  };
  localStorage.setItem(
    LLM_SETTINGS_STORAGE_KEY,
    JSON.stringify({
      selected_provider: llmSettingsState.selected_provider,
      provider_settings: llmSettingsState.provider_settings,
      admin_password: llmSettingsState.admin_password,
    }),
  );
}

function selectedProviderSettings(providerId = llmProvider.value) {
  return (llmSettingsState.provider_settings || {})[normalizeProviderId(providerId)] || {};
}

function selectedProviderApiKey(providerId = llmProvider.value) {
  const settings = selectedProviderSettings(providerId);
  return settings.api_key_saved === true ? String(settings.api_key || "").trim() : "";
}

function selectedProviderBaseUrl(providerId = llmProvider.value) {
  const normalizedProviderId = normalizeProviderId(providerId);
  if (normalizedProviderId === CUSTOM_PROVIDER_ID) {
    return String(customProviderSettings().base_url || "").trim();
  }
  return selectedProviderConfig()?.base_url || "";
}

function splitModelList(value) {
  return String(value || "")
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function customModelAllowed(provider = selectedProviderConfig()) {
  return Boolean(provider?.id === CUSTOM_PROVIDER_ID || llmModelsUnlocked || selectedProviderApiKey(provider?.id).trim());
}

function cssEscape(value) {
  if (window.CSS?.escape) {
    return window.CSS.escape(String(value || ""));
  }
  return String(value || "").replace(/["\\]/g, "\\$&");
}

function toggleSecretField(button) {
  const field = button.closest(".secret-field");
  const input = field?.querySelector("input");
  if (!input) {
    return;
  }
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  const label = show ? "Skrýt hodnotu" : "Zobrazit hodnotu";
  button.setAttribute("aria-label", label);
  button.title = label;
}

async function verifyUnlockPassword({ silent = false } = {}) {
  const password = llmUnlockPassword.value.trim();
  if (!password) {
    llmModelsUnlocked = false;
    refreshModelOptions(appSettings);
    if (!silent) {
      setUnlockStatus("Zadej odemykací heslo.", "error");
      statusEl.className = "status error";
      statusEl.textContent = "Zadej odemykací heslo.";
    }
    return false;
  }
  unlockModelsButton.disabled = true;
  if (!silent) {
    setUnlockStatus("Ověřuji heslo...");
  }
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
      setUnlockStatus("Modely jsou odemčené.", "success");
      statusEl.className = "status";
      statusEl.textContent = "Modely jsou odemčené.";
    }
    return true;
  } catch (error) {
    llmModelsUnlocked = false;
    refreshModelOptions(appSettings);
    if (!silent) {
      setUnlockStatus(error.message, "error");
      statusEl.className = "status error";
      statusEl.textContent = error.message;
    }
    return false;
  } finally {
    unlockModelsButton.disabled = false;
  }
}

function setUnlockStatus(message, variant = "") {
  if (!unlockModelsStatus) {
    return;
  }
  unlockModelsStatus.textContent = message;
  unlockModelsStatus.classList.toggle("success", variant === "success");
  unlockModelsStatus.classList.toggle("error", variant === "error");
}

function setModelRefreshStatus(message, variant = "") {
  if (!modelRefreshStatus) {
    return;
  }
  modelRefreshStatus.textContent = message;
  modelRefreshStatus.classList.toggle("success", variant === "success");
  modelRefreshStatus.classList.toggle("error", variant === "error");
}

async function refreshProviderModels() {
  const previousProvider = normalizeProviderId(llmProvider.value);
  const previousModel = selectedModelValue();
  const originalLabel = refreshModelsButton.textContent;
  console.info("[rag-avatar] LLM model refresh requested", {
    trigger: "manual-refresh",
    provider: previousProvider,
  });
  refreshModelsButton.disabled = true;
  refreshModelsButton.textContent = "Obnovuji...";
  setModelRefreshStatus("Obnovuji seznam modelů...");
  try {
    const response = await fetch("llm-providers/refresh", { method: "POST" });
    const data = await safeJson(response);
    if (!response.ok) {
      throw new Error(formatErrorDetail(data.detail || "Nepodařilo se obnovit seznam modelů."));
    }
    logLlmModelRefresh("manual-refresh", data);
    applyLlmSettingsUpdate(data, previousProvider);
    refreshModelOptions(appSettings);
    if (previousModel && Array.from(model.options).some((option) => option.value === previousModel)) {
      model.value = previousModel;
    }
    renderProviderApiKeyFields();
    const provider = selectedProviderConfig(appSettings);
    const modelCount = Array.isArray(provider?.model_presets) ? provider.model_presets.length : 0;
    setModelRefreshStatus(`Seznam modelů aktualizován (${modelCount} modelů).`, "success");
  } catch (error) {
    console.error("[rag-avatar] LLM model refresh failed", {
      trigger: "manual-refresh",
      provider: previousProvider,
      error,
    });
    setModelRefreshStatus(error.message, "error");
  } finally {
    refreshModelsButton.disabled = false;
    refreshModelsButton.textContent = originalLabel;
  }
}

function logLlmModelRefresh(trigger, settings) {
  const providers = Array.isArray(settings?.llm_providers) ? settings.llm_providers : [];
  console.info("[rag-avatar] LLM provider models loaded", {
    trigger,
    provider: settings?.llm_provider || "",
    model: settings?.llm_model || "",
    cache_ttl_seconds: settings?.llm_policy?.models_cache_ttl_seconds ?? null,
    providers: providers.map((provider) => ({
      id: provider.id,
      label: provider.label || provider.id,
      models: Array.isArray(provider.model_presets) ? provider.model_presets.length : 0,
      public_models: Array.isArray(provider.public_models) ? provider.public_models.length : 0,
      discover_models: provider.discover_models === true,
    })),
  });
}

function applyLlmSettingsUpdate(data, preferredProvider = llmProvider.value) {
  appSettings = {
    ...appSettings,
    llm_provider: data.llm_provider ?? appSettings.llm_provider,
    llm_base_url: data.llm_base_url ?? appSettings.llm_base_url,
    llm_model: data.llm_model ?? appSettings.llm_model,
    llm_providers: Array.isArray(data.llm_providers) ? data.llm_providers : appSettings.llm_providers,
    model_presets: Array.isArray(data.model_presets) ? data.model_presets : appSettings.model_presets,
    all_model_presets: Array.isArray(data.all_model_presets) ? data.all_model_presets : appSettings.all_model_presets,
    llm_policy: data.llm_policy && typeof data.llm_policy === "object" ? data.llm_policy : appSettings.llm_policy,
  };
  const providers = getLlmProviders(appSettings);
  const selectedProvider = providers.some((provider) => provider.id === normalizeProviderId(preferredProvider))
    ? normalizeProviderId(preferredProvider)
    : normalizeProviderId(appSettings.llm_provider || providers[0]?.id || "");
  populateProviderOptions(providers, selectedProvider);
  loadProviderValues(selectedProvider, { preferStored: true });
}

async function streamChat(payload) {
  return streamChatWithHandlers(payload, {
    onSources(data) {
      currentRetrievedChunks = data.retrieved_chunks || [];
      currentOmittedChunks = data.omitted_chunks || [];
      currentBudgetWarnings = data.chunk_budget_warnings || [];
      currentTokenBudget = data.token_budget || null;
      currentConversationSummary = data.conversation_summary || "";
      currentAnswerSources = data.sources || chunksToSources(currentRetrievedChunks);
      renderSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
      statusEl.textContent = `Nalezeno ${currentRetrievedChunks.length} chunků, odpovídám...`;
    },
    onToken(token) {
      streamedAnswerText += token;
      renderAnswer(streamedAnswerText);
    },
  });
}

function populateTokenBudgetFields(settings = appSettings) {
  const defaults = settings.token_budget_defaults || {};
  const stored = loadTokenBudgetSettings();
  contextWindowTokens.value = stored.context_window_tokens ?? defaults.context_window_tokens ?? 32768;
  outputBudgetShort.value = stored.output_token_budget_short ?? defaults.output_token_budget_short ?? 384;
  outputBudgetMedium.value = stored.output_token_budget_medium ?? defaults.output_token_budget_medium ?? 768;
  outputBudgetLong.value = stored.output_token_budget_long ?? defaults.output_token_budget_long ?? 1024;
  minPromptChunks.value = stored.min_prompt_chunks ?? defaults.min_prompt_chunks ?? 3;
  tokenBudgetSafetyMargin.value = stored.token_budget_safety_margin ?? defaults.token_budget_safety_margin ?? 0.1;
  conversationSummaryTriggerTokens.value =
    stored.conversation_summary_trigger_tokens ?? defaults.conversation_summary_trigger_tokens ?? 3000;
}

function loadTokenBudgetSettings() {
  try {
    const raw = JSON.parse(localStorage.getItem(TOKEN_BUDGET_STORAGE_KEY) || "{}");
    return raw && typeof raw === "object" ? raw : {};
  } catch {
    return {};
  }
}

function persistTokenBudgetSettings() {
  localStorage.setItem(TOKEN_BUDGET_STORAGE_KEY, JSON.stringify(currentTokenBudgetSettings()));
}

function currentTokenBudgetSettings() {
  return {
    context_window_tokens: nullableInteger(contextWindowTokens.value),
    output_token_budget_short: nullableInteger(outputBudgetShort.value),
    output_token_budget_medium: nullableInteger(outputBudgetMedium.value),
    output_token_budget_long: nullableInteger(outputBudgetLong.value),
    min_prompt_chunks: nullableInteger(minPromptChunks.value),
    token_budget_safety_margin: nullableNumber(tokenBudgetSafetyMargin.value),
    conversation_summary_trigger_tokens: nullableInteger(conversationSummaryTriggerTokens.value),
  };
}

async function chatRequest(payload, handlers = {}) {
  if (providerSupportsStreaming(payload.llm_provider)) {
    return streamChatWithHandlers(payload, handlers);
  }
  const data = await fetchChat(payload);
  handlers.onSources?.(data);
  if (data.answer) {
    handlers.onToken?.(data.answer, data);
  }
  handlers.onDone?.(data);
  return data;
}

async function fetchChat(payload) {
  const response = await fetch("chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await safeJson(response);
  if (!response.ok) {
    throw new Error(formatErrorDetail(data.detail || "Request failed"));
  }
  return data;
}

function providerSupportsStreaming(providerId = null) {
  const provider = getLlmProviders(appSettings).find(
    (item) => item.id === normalizeProviderId(providerId || llmProvider.value || appSettings.llm_provider || ""),
  );
  return provider?.supports_streaming !== false;
}

async function streamChatWithHandlers(payload, handlers = {}) {
  const response = await fetch("chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const data = await safeJson(response);
    throw new Error(formatErrorDetail(data.detail || "Request failed"));
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
      if (event.event === "preliminary_sources") {
        handlers.onPreliminarySources?.(event.data);
      } else if (event.event === "rerank_progress") {
        handlers.onRerankProgress?.(event.data);
      } else if (event.event === "sources") {
        handlers.onSources?.(event.data);
      } else if (event.event === "token") {
        handlers.onToken?.(event.data.text || "", event.data);
      } else if (event.event === "done") {
        donePayload = event.data;
        handlers.onDone?.(donePayload);
      } else if (event.event === "error") {
        throw new Error(formatErrorDetail(event.data.detail || "Streaming failed"));
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

function populateProviderOptions(providers, currentProvider) {
  const uniqueProviders = Array.isArray(providers)
    ? providers.filter(Boolean).filter((provider, index, items) => items.findIndex((item) => item.id === provider.id) === index)
    : [];
  llmProvider.innerHTML = uniqueProviders
    .map((provider) => `<option value="${escapeHtml(provider.id)}">${escapeHtml(provider.label || provider.id)}</option>`)
    .join("");
  const resolvedCurrentProvider = normalizeProviderId(currentProvider);
  llmProvider.value = uniqueProviders.some((provider) => provider.id === resolvedCurrentProvider)
    ? resolvedCurrentProvider
    : uniqueProviders[0]?.id || "";
}

function selectedProviderConfig(settings = appSettings) {
  const providers = getLlmProviders(settings);
  const providerId = normalizeProviderId(llmProvider?.value || settings.llm_provider || "");
  return providers.find((provider) => provider.id === providerId) || providers[0] || null;
}

function providerPublicModels(provider = selectedProviderConfig(), settings = appSettings) {
  if (!provider) {
    return [];
  }
  const providerModels = new Set(Array.isArray(provider?.model_presets) ? provider.model_presets.filter(Boolean) : []);
  const publicModels = Array.isArray(provider?.public_models) ? provider.public_models.filter(Boolean) : [];
  return publicModels.filter((model) => providerModels.has(model));
}

function loadProviderValues(providerId, { preferStored = false } = {}) {
  const provider = getLlmProviders(appSettings).find((item) => item.id === providerId) || null;
  const providerSettings = (llmSettingsState.provider_settings || {})[providerId] || {};
  const baseUrl = preferStored && providerSettings.base_url ? providerSettings.base_url : provider?.base_url || "";
  const customModelValue = providerSettings.custom_model || "";
  llmProvider.value = providerId || provider?.id || "";
  llmBaseUrl.value = baseUrl;
  llmApiKey.value = "";
  customModel.value = customModelValue;
}

function providerLabelForId(providerId) {
  const normalized = normalizeProviderId(providerId);
  const provider = getLlmProviders(appSettings).find((item) => item.id === normalized);
  return provider?.label || normalized || "—";
}

function populateModels(presets, currentModel, allowCustom = false) {
  const uniqueModels = Array.from(new Set(presets.filter(Boolean)));
  const options = uniqueModels.map((modelName) => `<option value="${escapeHtml(modelName)}">${escapeHtml(modelName)}</option>`);
  if (allowCustom) {
    options.push(`<option value="${escapeHtml(CUSTOM_MODEL_VALUE)}">Jiný</option>`);
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
  const provider = selectedProviderConfig(settings);
  const providerModels = Array.isArray(provider?.model_presets) ? provider.model_presets.filter(Boolean) : [];
  const publicModels = providerPublicModels(provider, settings);
  const browserApiKeyProvided = Boolean(selectedProviderApiKey(provider?.id));
  const unlocked = customModelAllowed(provider);
  const currentModel = model.value === CUSTOM_MODEL_VALUE ? customModel.value.trim() : model.value || provider?.default_model || "";
  populateModels(unlocked ? providerModels : publicModels, currentModel, unlocked);
  const providerBaseUrl = provider?.base_url || "";
  llmBaseUrl.value = selectedProviderBaseUrl(provider?.id) || providerBaseUrl;
  updateLlmPolicyNote(settings.llm_policy, unlocked, browserApiKeyProvided);
}

// System placeholders are filled by the server and never surfaced as a control.
const SYSTEM_PLACEHOLDERS = new Set(["question", "context", "current_date"]);

// Merged effective global placeholder defs from /settings (DEFAULT_PLACEHOLDERS
// overlaid by placeholders.json), keyed by name.
function globalPlaceholderDefs() {
  const records = Array.isArray(appSettings.placeholders) ? appSettings.placeholders : [];
  const defs = {};
  for (const record of records) {
    if (record && record.name) {
      defs[String(record.name)] = record;
    }
  }
  return defs;
}

// Browser-local global placeholder defs (name -> def). These sit between the
// selected prompt's inline defs and the shared server overlay in resolution.
function localGlobalPlaceholderDefs() {
  return localPlaceholderDefs && typeof localPlaceholderDefs === "object" ? localPlaceholderDefs : {};
}

// Inline placeholder defs declared on the currently selected prompt; these
// override the global defs wholesale.
function activePromptInlinePlaceholderDefs() {
  const preset = getPromptPresetById(activePromptPresetId);
  const inline = preset && preset.placeholders;
  return inline && typeof inline === "object" && !Array.isArray(inline) ? inline : {};
}

// Resolve the parameter placeholders used by the current prompt text: parse the
// {tokens} from the system + user templates, drop system placeholders, and for
// each remaining token take its def wholesale from the most specific scope:
// inline (selected prompt) -> browser-local global -> shared server overlay
// (DEFAULT_PLACEHOLDERS already merged into appSettings.placeholders). Tokens with
// no def anywhere get no control (they render literally).
function resolveActivePlaceholderDefs() {
  const tokens = new Set([
    ...extractPromptVariables(systemPrompt.value),
    ...extractPromptVariables(userPromptTemplate.value),
  ]);
  const inline = activePromptInlinePlaceholderDefs();
  const local = localGlobalPlaceholderDefs();
  const globals = globalPlaceholderDefs();
  const resolved = {};
  for (const token of tokens) {
    if (SYSTEM_PLACEHOLDERS.has(token)) {
      continue;
    }
    const def = inline[token] || local[token] || globals[token];
    if (def) {
      resolved[token] = def;
    }
  }
  return resolved;
}

// Effective resolved def for a single placeholder name (inline -> local -> shared
// overlay). Used to build the chat request's effective placeholder_defs.
function effectivePlaceholderDef(name) {
  return activePromptInlinePlaceholderDefs()[name]
    || localGlobalPlaceholderDefs()[name]
    || globalPlaceholderDefs()[name]
    || null;
}

// Build the placeholder_defs map sent on a chat request. Carries the FULLY
// RESOLVED effective def (inline -> browser-local global -> shared overlay) for
// each parameter placeholder the prompt uses, not just inline defs. The server is
// stateless about localStorage, so it treats placeholder_defs as the highest
// precedence source; sending effective defs makes it substitute exactly what the
// user configured here (its own overlay + code floor remain a harmless fallback).
function effectivePlaceholderDefsForRequest() {
  const defs = {};
  for (const name of Object.keys(activePlaceholderDefs)) {
    const def = effectivePlaceholderDef(name);
    if (def) {
      defs[name] = def;
    }
  }
  return defs;
}

function placeholderDefaultValue(def) {
  return typeof def?.default === "string" ? def.default : "";
}

// ---------------------------------------------------------------------------
// Placeholder definition editor (Task 14d)
//
// Manages placeholder DEFINITIONS (not the per-question selections) at two
// scopes: global (shared server overlay via /placeholders + browser-local in
// localStorage) and inline (on the selected prompt preset). Reuses one dialog
// editor for every scope.
// ---------------------------------------------------------------------------

function loadLocalPlaceholderDefs() {
  try {
    const raw = JSON.parse(localStorage.getItem(LOCAL_PLACEHOLDER_DEFS_STORAGE_KEY) || "{}");
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
      return {};
    }
    const defs = {};
    for (const [name, def] of Object.entries(raw)) {
      const normalized = normalizePlaceholderDef(name, def);
      if (normalized) {
        defs[normalized.name] = normalized.def;
      }
    }
    return defs;
  } catch {
    return {};
  }
}

function persistLocalPlaceholderDefs() {
  localStorage.setItem(LOCAL_PLACEHOLDER_DEFS_STORAGE_KEY, JSON.stringify(localPlaceholderDefs));
}

// Coerce an arbitrary stored object into a clean {name, def} pair, or null.
function normalizePlaceholderDef(name, def) {
  const slug = slugifyPlaceholderName(name);
  if (!slug || !def || typeof def !== "object") {
    return null;
  }
  const kind = def.kind === "select" ? "select" : "text";
  const options = kind === "select" && Array.isArray(def.options)
    ? def.options
        .map((option) => {
          const optionName = String(option?.name || "").trim();
          if (!optionName) {
            return null;
          }
          return {
            name: optionName,
            label: String(option?.label || optionName).trim(),
            text: String(option?.text || ""),
          };
        })
        .filter(Boolean)
    : [];
  const help = def.help != null && String(def.help).trim() ? String(def.help).trim() : null;
  return {
    name: slug,
    def: {
      label: String(def.label || slug).trim(),
      kind,
      help,
      default: String(def.default || ""),
      options,
    },
  };
}

function slugifyPlaceholderName(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

// After any def change (global or inline) re-fetch the merged globals from the
// server, then re-render the lists and the active main-page controls so changes
// show immediately.
async function refreshAfterPlaceholderDefChange() {
  try {
    const response = await fetch("settings");
    if (response.ok) {
      const settings = await response.json();
      appSettings = { ...appSettings, placeholders: settings.placeholders };
    }
  } catch (error) {
    console.warn("Could not refresh settings after placeholder def change", error);
  }
  renderPlaceholderControls();
  renderGlobalPlaceholderDefs();
  renderInlinePlaceholderDefs();
}

// Describe where an effective global def currently comes from, for the list.
function globalPlaceholderDefSource(name) {
  if (Object.prototype.hasOwnProperty.call(localGlobalPlaceholderDefs(), name)) {
    return "local";
  }
  const record = (Array.isArray(appSettings.placeholders) ? appSettings.placeholders : [])
    .find((item) => item && item.name === name);
  if (record && (record.owner_id || record.updated_at)) {
    return "shared";
  }
  return "builtin";
}

const PLACEHOLDER_SOURCE_LABELS = {
  local: "lokální (jen tento prohlížeč)",
  shared: "sdílená (server)",
  builtin: "vestavěná",
};

function renderGlobalPlaceholderDefs() {
  if (!globalPlaceholderDefsList) {
    return;
  }
  // Union of merged server globals + browser-local globals, deduped by name.
  const names = new Set([
    ...Object.keys(globalPlaceholderDefs()),
    ...Object.keys(localGlobalPlaceholderDefs()),
  ]);
  const sorted = Array.from(names).sort();
  globalPlaceholderDefsList.innerHTML = sorted
    .map((name) => {
      const source = globalPlaceholderDefSource(name);
      const def = localGlobalPlaceholderDefs()[name] || globalPlaceholderDefs()[name] || {};
      const sourceLabel = PLACEHOLDER_SOURCE_LABELS[source] || source;
      const kindLabel = def.kind === "select" ? "výběr" : "text";
      return `
        <div class="placeholder-def-row" data-global-placeholder="${escapeHtml(name)}">
          <div class="placeholder-def-meta">
            <strong>${escapeHtml(def.label || name)}</strong>
            <code>{${escapeHtml(name)}}</code>
            <span class="field-note">${escapeHtml(kindLabel)} · ${escapeHtml(sourceLabel)}</span>
          </div>
          <div class="inline-actions">
            <button class="secondary" type="button" data-edit-global="${escapeHtml(name)}" data-edit-scope="local">Upravit lokálně</button>
            <button class="secondary" type="button" data-edit-global="${escapeHtml(name)}" data-edit-scope="shared">Upravit sdíleně</button>
            ${source === "builtin"
              ? ""
              : `<button class="secondary danger-lite" type="button" data-delete-global="${escapeHtml(name)}" data-delete-scope="${source}">Smazat</button>`}
          </div>
        </div>`;
    })
    .join("");
}

function renderInlinePlaceholderDefs() {
  if (!inlinePlaceholderDefsList) {
    return;
  }
  const inline = activePromptInlinePlaceholderDefs();
  const names = Object.keys(inline).sort();
  if (!names.length) {
    inlinePlaceholderDefsList.innerHTML = `<p class="field-note">Tento prompt nemá žádné vlastní proměnné.</p>`;
    return;
  }
  inlinePlaceholderDefsList.innerHTML = names
    .map((name) => {
      const def = inline[name] || {};
      const kindLabel = def.kind === "select" ? "výběr" : "text";
      return `
        <div class="placeholder-def-row" data-inline-placeholder="${escapeHtml(name)}">
          <div class="placeholder-def-meta">
            <strong>${escapeHtml(def.label || name)}</strong>
            <code>{${escapeHtml(name)}}</code>
            <span class="field-note">${escapeHtml(kindLabel)} · inline</span>
          </div>
          <div class="inline-actions">
            <button class="secondary" type="button" data-edit-inline="${escapeHtml(name)}">Upravit</button>
            <button class="secondary danger-lite" type="button" data-delete-inline="${escapeHtml(name)}">Smazat</button>
          </div>
        </div>`;
    })
    .join("");
}

// --- shared dialog editor ---------------------------------------------------
// editorContext describes where the result is saved:
//   { scope: "global-local" | "global-shared" | "inline", originalName }
let placeholderEditorContext = null;

function openPlaceholderDefEditor(context, def) {
  placeholderEditorContext = context;
  const isNew = !context.originalName;
  placeholderDefName.value = context.originalName || "";
  placeholderDefLabel.value = def?.label || "";
  placeholderDefHelp.value = def?.help || "";
  placeholderDefKind.value = def?.kind === "select" ? "select" : "text";
  placeholderDefDefaultText.value = def?.kind === "select" ? "" : (def?.default || "");
  placeholderDefDefaultSelect.value = def?.kind === "select" ? (def?.default || "") : "";
  renderPlaceholderOptionRows(def?.kind === "select" && Array.isArray(def.options) ? def.options : []);
  updatePlaceholderKindVisibility();
  setPlaceholderDefError("");
  placeholderDefTitle.textContent = isNew ? "Nová proměnná" : "Upravit proměnnou";
  placeholderDefScopeNote.textContent = placeholderScopeNote(context.scope);
  renderPlaceholderDefActions(context.scope, isNew);
  placeholderDefDialog.showModal();
  placeholderDefName.focus();
}

function placeholderScopeNote(scope) {
  if (scope === "global-local") {
    return "Globální proměnná uložená jen v tomto prohlížeči.";
  }
  if (scope === "global-shared") {
    return "Globální proměnná sdílená přes server (vyžaduje vlastnictví nebo admin heslo).";
  }
  return "Inline proměnná tohoto promptu (přebije globální). Uloží se až při uložení promptu.";
}

// Default action is "save as new" so editing does not silently shadow a shared
// def; updating an existing name is the explicit secondary action.
function renderPlaceholderDefActions(scope, isNew) {
  const saveLabel = scope === "inline" ? "Uložit jako novou inline" : "Uložit jako novou";
  const updateLabel = "Aktualizovat tuto";
  const actions = [`<button class="secondary" type="button" data-def-action="save-new">${escapeHtml(saveLabel)}</button>`];
  if (!isNew) {
    actions.push(`<button class="secondary" type="button" data-def-action="update">${escapeHtml(updateLabel)}</button>`);
  }
  placeholderDefActions.innerHTML = actions.join("");
}

function updatePlaceholderKindVisibility() {
  const isSelect = placeholderDefKind.value === "select";
  placeholderDefDefaultTextField.hidden = isSelect;
  placeholderDefDefaultSelectField.hidden = !isSelect;
  placeholderDefOptionsBlock.hidden = !isSelect;
}

function renderPlaceholderOptionRows(options) {
  placeholderDefOptionsList.innerHTML = (options.length ? options : [{ name: "", label: "", text: "" }])
    .map((option) => placeholderOptionRowHtml(option))
    .join("");
}

function placeholderOptionRowHtml(option) {
  return `
    <div class="placeholder-def-option-row">
      <input type="text" data-option-field="name" placeholder="název" value="${escapeHtml(option?.name || "")}" autocomplete="off" />
      <input type="text" data-option-field="label" placeholder="popisek" value="${escapeHtml(option?.label || "")}" autocomplete="off" />
      <textarea data-option-field="text" rows="2" placeholder="vložený text">${escapeHtml(option?.text || "")}</textarea>
      <button class="secondary danger-lite" type="button" data-remove-option>×</button>
    </div>`;
}

function collectPlaceholderOptionRows() {
  return Array.from(placeholderDefOptionsList.querySelectorAll(".placeholder-def-option-row"))
    .map((row) => ({
      name: row.querySelector('[data-option-field="name"]')?.value || "",
      label: row.querySelector('[data-option-field="label"]')?.value || "",
      text: row.querySelector('[data-option-field="text"]')?.value || "",
    }))
    .filter((option) => option.name.trim());
}

function setPlaceholderDefError(message) {
  if (!placeholderDefError) {
    return;
  }
  placeholderDefError.hidden = !message;
  placeholderDefError.textContent = message || "";
}

// Build a {name, def} from the dialog inputs, or null with an error shown.
function readPlaceholderDefFromEditor() {
  const slug = slugifyPlaceholderName(placeholderDefName.value);
  if (!slug) {
    setPlaceholderDefError("Zadej platný název (písmena, číslice, podtržítka).");
    return null;
  }
  const kind = placeholderDefKind.value === "select" ? "select" : "text";
  const options = kind === "select" ? collectPlaceholderOptionRows() : [];
  if (kind === "select" && !options.length) {
    setPlaceholderDefError("Výběr potřebuje aspoň jednu možnost.");
    return null;
  }
  const help = placeholderDefHelp.value.trim() ? placeholderDefHelp.value.trim() : null;
  const def = {
    label: placeholderDefLabel.value.trim() || slug,
    kind,
    help,
    default: kind === "select" ? placeholderDefDefaultSelect.value.trim() : placeholderDefDefaultText.value,
    options,
  };
  return { name: slug, def };
}

async function submitPlaceholderDefEditor(action) {
  const result = readPlaceholderDefFromEditor();
  if (!result) {
    return;
  }
  const context = placeholderEditorContext || {};
  // "update" keeps the original name; "save-new" uses the typed name and refuses
  // to silently overwrite an existing entry in the same scope.
  const targetName = action === "update" && context.originalName ? context.originalName : result.name;
  try {
    if (context.scope === "global-local") {
      saveLocalGlobalPlaceholderDef(targetName, result.def, action);
    } else if (context.scope === "global-shared") {
      await saveSharedGlobalPlaceholderDef(targetName, result.def, action);
    } else {
      saveInlinePlaceholderDef(targetName, result.def, action);
    }
  } catch (error) {
    setPlaceholderDefError(error.message);
    return;
  }
  placeholderDefDialog.close();
  await refreshAfterPlaceholderDefChange();
}

function saveLocalGlobalPlaceholderDef(name, def, action) {
  if (action === "save-new" && Object.prototype.hasOwnProperty.call(localPlaceholderDefs, name)) {
    throw new Error(`Lokální proměnná "${name}" už existuje. Použij „Aktualizovat tuto“.`);
  }
  const normalized = normalizePlaceholderDef(name, def);
  if (!normalized) {
    throw new Error("Proměnnou se nepodařilo uložit.");
  }
  localPlaceholderDefs = { ...localPlaceholderDefs, [normalized.name]: normalized.def };
  persistLocalPlaceholderDefs();
}

async function saveSharedGlobalPlaceholderDef(name, def, action) {
  const existing = (Array.isArray(appSettings.placeholders) ? appSettings.placeholders : [])
    .find((item) => item && item.name === name && (item.owner_id || item.updated_at));
  if (action === "save-new" && existing) {
    throw new Error(`Sdílená proměnná "${name}" už existuje. Použij „Aktualizovat tuto“.`);
  }
  const payload = {
    name,
    label: def.label,
    kind: def.kind,
    help: def.help,
    default: def.default,
    options: def.options,
    owner_id: getBrowserOwnerId(),
    admin_password: llmUnlockPassword.value.trim() || null,
  };
  const response = await fetch("placeholders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await safeJson(response);
  if (!response.ok) {
    throw new Error(data.detail || "Uložení sdílené proměnné selhalo.");
  }
}

// Inline defs live on the selected prompt preset. We mutate the in-memory preset's
// placeholders map; the change persists when the user saves the prompt (save-as-new
// / update), matching how the rest of the prompt editor works.
function saveInlinePlaceholderDef(name, def, action) {
  const preset = getPromptPresetById(activePromptPresetId);
  if (!preset) {
    throw new Error("Nejdřív vyber prompt.");
  }
  if (isBuiltInPromptPreset(activePromptPresetId)) {
    throw new Error("Vestavěný prompt nelze upravit. Ulož ho nejdřív jako nový prompt.");
  }
  if (!preset.placeholders || typeof preset.placeholders !== "object" || Array.isArray(preset.placeholders)) {
    preset.placeholders = {};
  }
  if (action === "save-new" && Object.prototype.hasOwnProperty.call(preset.placeholders, name)) {
    throw new Error(`Inline proměnná "${name}" už existuje. Použij „Aktualizovat tuto“.`);
  }
  const normalized = normalizePlaceholderDef(name, def);
  if (!normalized) {
    throw new Error("Proměnnou se nepodařilo uložit.");
  }
  preset.placeholders[normalized.name] = normalized.def;
  // Persist immediately for editable local presets so an inline def is not lost if
  // the user forgets to re-save; server presets persist on the next prompt save.
  if (isLocalPromptPreset(activePromptPresetId)) {
    persistLocalPromptPresets();
  }
}

function deleteLocalGlobalPlaceholderDef(name) {
  if (!Object.prototype.hasOwnProperty.call(localPlaceholderDefs, name)) {
    return;
  }
  const next = { ...localPlaceholderDefs };
  delete next[name];
  localPlaceholderDefs = next;
  persistLocalPlaceholderDefs();
}

async function deleteSharedGlobalPlaceholderDef(name) {
  const params = new URLSearchParams({ owner_id: getBrowserOwnerId() });
  const adminPassword = llmUnlockPassword.value.trim();
  if (adminPassword) {
    params.set("admin_password", adminPassword);
  }
  const response = await fetch(`placeholders/${encodeURIComponent(name)}?${params.toString()}`, {
    method: "DELETE",
  });
  if (!response.ok && response.status !== 404) {
    const data = await safeJson(response);
    throw new Error(data.detail || "Smazání sdílené proměnné selhalo.");
  }
}

function deleteInlinePlaceholderDef(name) {
  const preset = getPromptPresetById(activePromptPresetId);
  if (!preset || !preset.placeholders) {
    return;
  }
  delete preset.placeholders[name];
  if (isLocalPromptPreset(activePromptPresetId)) {
    persistLocalPromptPresets();
  }
}

// --- editor event wiring ----------------------------------------------------
newGlobalPlaceholderButton?.addEventListener("click", () => {
  openPlaceholderDefEditor({ scope: "global-local", originalName: "" }, null);
});
newInlinePlaceholderButton?.addEventListener("click", () => {
  if (isBuiltInPromptPreset(activePromptPresetId)) {
    statusEl.className = "status error";
    statusEl.textContent = "Vestavěný prompt nelze upravit. Ulož ho nejdřív jako nový prompt.";
    return;
  }
  openPlaceholderDefEditor({ scope: "inline", originalName: "" }, null);
});

globalPlaceholderDefsList?.addEventListener("click", async (event) => {
  const editButton = event.target.closest("[data-edit-global]");
  if (editButton) {
    const name = editButton.dataset.editGlobal;
    const scope = editButton.dataset.editScope === "shared" ? "global-shared" : "global-local";
    const def = localGlobalPlaceholderDefs()[name] || globalPlaceholderDefs()[name] || null;
    // Editing a built-in/shared into local scope starts from its current def but
    // creates a NEW browser-local entry (so default action is still save-as-new
    // unless the name already exists in that scope).
    const existsInScope = scope === "global-local"
      ? Object.prototype.hasOwnProperty.call(localGlobalPlaceholderDefs(), name)
      : Boolean((Array.isArray(appSettings.placeholders) ? appSettings.placeholders : [])
          .find((item) => item && item.name === name && (item.owner_id || item.updated_at)));
    openPlaceholderDefEditor({ scope, originalName: existsInScope ? name : "" }, def);
    if (!existsInScope) {
      placeholderDefName.value = name;
    }
    return;
  }
  const deleteButton = event.target.closest("[data-delete-global]");
  if (deleteButton) {
    const name = deleteButton.dataset.deleteGlobal;
    const scope = deleteButton.dataset.deleteScope;
    if (!window.confirm(`Smazat proměnnou "${name}"?`)) {
      return;
    }
    try {
      if (scope === "local") {
        deleteLocalGlobalPlaceholderDef(name);
      } else {
        await deleteSharedGlobalPlaceholderDef(name);
      }
      await refreshAfterPlaceholderDefChange();
    } catch (error) {
      statusEl.className = "status error";
      statusEl.textContent = error.message;
    }
  }
});

inlinePlaceholderDefsList?.addEventListener("click", async (event) => {
  const editButton = event.target.closest("[data-edit-inline]");
  if (editButton) {
    const name = editButton.dataset.editInline;
    const def = activePromptInlinePlaceholderDefs()[name] || null;
    openPlaceholderDefEditor({ scope: "inline", originalName: name }, def);
    return;
  }
  const deleteButton = event.target.closest("[data-delete-inline]");
  if (deleteButton) {
    const name = deleteButton.dataset.deleteInline;
    if (!window.confirm(`Smazat inline proměnnou "${name}"?`)) {
      return;
    }
    deleteInlinePlaceholderDef(name);
    await refreshAfterPlaceholderDefChange();
  }
});

placeholderDefKind?.addEventListener("change", updatePlaceholderKindVisibility);
addPlaceholderOptionButton?.addEventListener("click", () => {
  placeholderDefOptionsList.insertAdjacentHTML("beforeend", placeholderOptionRowHtml({}));
});
placeholderDefOptionsList?.addEventListener("click", (event) => {
  const removeButton = event.target.closest("[data-remove-option]");
  if (removeButton) {
    removeButton.closest(".placeholder-def-option-row")?.remove();
  }
});
placeholderDefActions?.addEventListener("click", (event) => {
  const actionButton = event.target.closest("[data-def-action]");
  if (actionButton) {
    submitPlaceholderDefEditor(actionButton.dataset.defAction);
  }
});
closePlaceholderDefButton?.addEventListener("click", () => placeholderDefDialog.close());
placeholderDefForm?.addEventListener("submit", (event) => event.preventDefault());

// Re-render the main-page controls for the active prompt and reset every value to
// its resolved def default. Called on every prompt switch and on prompt-text edits.
function renderPlaceholderControls() {
  activePlaceholderDefs = resolveActivePlaceholderDefs();
  placeholderSelections = {};
  if (!placeholderControls) {
    return;
  }
  const entries = Object.entries(activePlaceholderDefs);
  placeholderControls.innerHTML = entries
    .map(([name, def]) => renderPlaceholderControl(name, def))
    .join("");
  for (const [name, def] of entries) {
    placeholderSelections[name] = placeholderDefaultValue(def);
    const control = placeholderControls.querySelector(`[data-placeholder="${cssAttrEscape(name)}"]`);
    if (!control) {
      continue;
    }
    control.value = placeholderSelections[name];
    if (def.kind === "select") {
      // If the def default option name is unknown, the browser keeps the first
      // option selected; sync the stored value to whatever is actually selected.
      placeholderSelections[name] = control.value;
    }
    control.addEventListener(def.kind === "select" ? "change" : "input", () => {
      placeholderSelections[name] = control.value;
    });
  }
}

function renderPlaceholderControl(name, def) {
  const label = escapeHtml(def.label || name);
  const help = def.help ? `<small class="field-note">${escapeHtml(def.help)}</small>` : "";
  if (def.kind === "select") {
    const options = (Array.isArray(def.options) ? def.options : [])
      .map((option) => `<option value="${escapeHtml(option.name)}">${escapeHtml(option.label || option.name)}</option>`)
      .join("");
    return `
      <label class="field placeholder-control-field">
        <span>${label}</span>
        <select data-placeholder="${escapeHtml(name)}">${options}</select>
        ${help}
      </label>`;
  }
  return `
    <label class="field placeholder-control-field">
      <span>${label}</span>
      <textarea data-placeholder="${escapeHtml(name)}" rows="2"></textarea>
      ${help}
    </label>`;
}

function cssAttrEscape(value) {
  return String(value).replace(/["\\]/g, "\\$&");
}

// Apply saved history selections on top of freshly rendered controls: keep values
// for placeholders that still exist, ignore those whose placeholder is gone, and
// leave the def default where a saved value is missing.
function applyPlaceholderSelections(savedSelections) {
  const saved = savedSelections && typeof savedSelections === "object" ? savedSelections : {};
  for (const [name, def] of Object.entries(activePlaceholderDefs)) {
    if (!Object.prototype.hasOwnProperty.call(saved, name)) {
      continue;
    }
    const value = String(saved[name] ?? "");
    const control = placeholderControls?.querySelector(`[data-placeholder="${cssAttrEscape(name)}"]`);
    if (def.kind === "select") {
      const allowed = (Array.isArray(def.options) ? def.options : []).some((option) => option.name === value);
      if (!allowed) {
        continue;
      }
    }
    placeholderSelections[name] = value;
    if (control) {
      control.value = value;
    }
  }
}

function updatePromptTemplateWarning() {
  const unknownVariables = unknownPromptVariables([
    systemPrompt.value,
    userPromptTemplate.value,
  ]);
  if (!unknownVariables.length) {
    promptTemplateWarning.hidden = true;
    promptTemplateWarning.textContent = "";
    return;
  }
  promptTemplateWarning.hidden = false;
  promptTemplateWarning.textContent =
    `Neznámé proměnné v promptu: ${unknownVariables.map((name) => `{${name}}`).join(", ")}. ` +
    "Prompt lze uložit; neznámé proměnné zůstanou v odeslaném promptu beze změny.";
}

function unknownPromptVariables(templates) {
  const unknown = new Set();
  const inline = activePromptInlinePlaceholderDefs();
  const local = localGlobalPlaceholderDefs();
  const globals = globalPlaceholderDefs();
  templates.forEach((template) => {
    extractPromptVariables(template).forEach((name) => {
      // Known if it is a system/code-floor placeholder, or resolves to any def.
      const known = KNOWN_PROMPT_VARIABLES.has(name)
        || Object.prototype.hasOwnProperty.call(inline, name)
        || Object.prototype.hasOwnProperty.call(local, name)
        || Object.prototype.hasOwnProperty.call(globals, name);
      if (!known) {
        unknown.add(name);
      }
    });
  });
  return Array.from(unknown).sort();
}

function extractPromptVariables(template) {
  const variables = [];
  const pattern = /\{([A-Za-z_][A-Za-z0-9_]*)(?:![rsa])?(?::[^{}]*)?\}/g;
  let match;
  while ((match = pattern.exec(template || "")) !== null) {
    variables.push(match[1]);
  }
  return variables;
}

async function loadPromptPresets(selectedId = activePromptPresetId || defaultPromptPresetId()) {
  localPromptPresets = loadLocalPromptPresets();
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
  applyPromptPresetById(selectedId);
}

function renderPromptPresets(selectedId = activePromptPresetId || defaultPromptPresetId()) {
  const resolvedId = normalizePromptPresetId(selectedId);
  renderPromptPresetSelect(activePromptPreset, resolvedId);
  renderPromptPresetSelect(promptPreset, resolvedId);
  activePromptPresetId = resolvedId;
  deletePromptButton.disabled = !isEditablePromptPreset(resolvedId);
  updatePromptButton.disabled = !isEditablePromptPreset(resolvedId);
}

function renderPromptPresetSelect(selectEl, selectedId) {
  const wpLocal = localPromptPresets.filter((preset) => presetWpId(preset) === activeWpId);
  const wpServer = promptPresets.filter((preset) => presetWpId(preset) === activeWpId);
  const builtinOptions = builtInPromptPresets()
    .map((preset) => `<option value="${escapeHtml(preset.id)}">${escapeHtml(preset.name)}</option>`)
    .join("");
  const localOptions = wpLocal.length
    ? `<optgroup label="Lokální prompty">${wpLocal
        .map((preset) => `<option value="${escapeHtml(preset.id)}">Local - ${escapeHtml(preset.name)}</option>`)
        .join("")}</optgroup>`
    : "";
  const serverOptions = wpServer.length
    ? `<optgroup label="Sdílené prompty">${wpServer
        .map((preset) => {
          const ownedSuffix = isOwnedServerPromptPreset(preset.id) ? " (tvůj)" : "";
          return `<option value="${escapeHtml(preset.id)}">Shared - ${escapeHtml(preset.name)}${ownedSuffix}</option>`;
        })
        .join("")}</optgroup>`
    : "";
  selectEl.innerHTML = `<optgroup label="Vestavěné prompty">${builtinOptions}</optgroup>${localOptions}${serverOptions}`;
  selectEl.value = normalizePromptPresetId(selectedId);
}

function presetWpId(preset) {
  return resolveWpId(preset?.wp_id);
}

function promptPresetExists(presetId) {
  return Boolean(getPromptPresetById(presetId));
}

function normalizePromptPresetId(presetId) {
  if (presetId === LEGACY_DEFAULT_PROMPT_PRESET_ID) {
    return defaultPromptPresetId();
  }
  return promptPresetExists(presetId) ? presetId : defaultPromptPresetId();
}

function isBuiltInPromptPreset(presetId) {
  return allBuiltInPromptPresets().some((preset) => preset.id === presetId);
}

function isLocalPromptPreset(presetId) {
  return String(presetId || "").startsWith(LOCAL_PROMPT_PREFIX)
    && localPromptPresets.some((preset) => preset.id === presetId);
}

function isServerPromptPreset(presetId) {
  return !isBuiltInPromptPreset(presetId)
    && !String(presetId || "").startsWith(LOCAL_PROMPT_PREFIX)
    && promptPresets.some((preset) => preset.id === presetId);
}

function isEditablePromptPreset(presetId) {
  return isLocalPromptPreset(presetId) || isServerPromptPreset(presetId);
}

// Built-in prompts are shipped per WP by the backend (appSettings.wps). Each may
// carry an inline `placeholders` map that overrides the global defs wholesale.
function wpBuiltInPromptPresets(wp) {
  if (!wp) {
    return [];
  }
  return (wp.builtin_prompts || []).map((preset) => ({
    id: preset.id,
    name: preset.name,
    wp_id: wp.id,
    system_prompt: preset.system_prompt || "",
    user_prompt_template: preset.user_prompt_template || "",
    placeholders: preset.placeholders && typeof preset.placeholders === "object" ? preset.placeholders : {},
  }));
}

function builtInPromptPresets(wpId = activeWpId) {
  return wpBuiltInPromptPresets(getWpConfig(wpId));
}

function allBuiltInPromptPresets() {
  return getWpConfigs().flatMap((wp) => wpBuiltInPromptPresets(wp));
}

function defaultPromptPresetId(wpId = activeWpId) {
  const wp = getWpConfig(wpId);
  return wp?.default_prompt_id || wpBuiltInPromptPresets(wp)[0]?.id || "";
}

function getPromptPresetById(presetId) {
  if (presetId === LEGACY_DEFAULT_PROMPT_PRESET_ID) {
    return getPromptPresetById(defaultPromptPresetId());
  }
  return allBuiltInPromptPresets().find((preset) => preset.id === presetId)
    || localPromptPresets.find((preset) => preset.id === presetId)
    || promptPresets.find((preset) => preset.id === presetId)
    || null;
}

function applySelectedPromptPreset() {
  applyPromptPresetById(promptPreset.value);
}

function applyPromptPresetById(presetId) {
  const resolvedId = normalizePromptPresetId(presetId);
  activePromptPresetId = resolvedId;
  const preset = getPromptPresetById(resolvedId);
  if (!preset) {
    resetPromptEditorValues();
    renderPromptPresets(defaultPromptPresetId());
    return;
  }
  systemPrompt.value = preset.system_prompt || "";
  userPromptTemplate.value = preset.user_prompt_template || "";
  // Switching prompts resets controls to the new prompt's resolved defaults; no
  // prior values (including text placeholders) are preserved across the switch.
  renderPlaceholderControls();
  updatePromptTemplateWarning();
  renderInlinePlaceholderDefs();
  renderPromptPresets(resolvedId);
}

function activePromptPresetMetadata() {
  const preset = getPromptPresetById(activePromptPresetId);
  return {
    id: preset?.id || activePromptPresetId || defaultPromptPresetId(),
    name: preset?.name || activePromptPresetId || "Výchozí",
  };
}

function currentPromptDraft({ id = null, name }) {
  return {
    id,
    name: name.trim(),
    wp_id: activePromptWpId(),
    system_prompt: systemPrompt.value,
    user_prompt_template: userPromptTemplate.value,
    // Inline placeholder defs come from the live preset object, which the inline
    // def editor (14d) mutates in place; saving the prompt persists them.
    placeholders: activePromptInlinePlaceholderDefs(),
  };
}

function activePromptWpId() {
  // Drafts are saved under the currently selected WP.
  return resolveWpId(activeWpId);
}

async function saveCurrentPromptPreset({ mode }) {
  const isUpdate = mode === "update";
  const currentPreset = isUpdate && isServerPromptPreset(promptPreset.value)
    ? promptPresets.find((item) => item.id === promptPreset.value)
    : null;
  if (isUpdate && !currentPreset) {
    throw new Error("Vyber uložený prompt, který chceš aktualizovat.");
  }
  const proposedName = currentPreset?.name || "";
  const name = window.prompt("Název promptu", proposedName);
  if (!name || !name.trim()) {
    return;
  }
  const payload = {
    ...currentPromptDraft({ id: isUpdate ? currentPreset.id : null, name }),
    owner_id: getBrowserOwnerId(),
    admin_password: llmUnlockPassword.value.trim() || null,
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

async function saveCurrentPromptPresetLocally({ mode }) {
  const isUpdate = mode === "update";
  const currentPreset = isUpdate && isLocalPromptPreset(promptPreset.value)
    ? localPromptPresets.find((item) => item.id === promptPreset.value)
    : null;
  if (isUpdate && !currentPreset) {
    throw new Error("Vyber lokální prompt, který chceš aktualizovat.");
  }
  const proposedName = currentPreset?.name || "";
  const name = window.prompt("Název lokálního promptu", proposedName);
  if (!name || !name.trim()) {
    return;
  }
  const id = isUpdate ? currentPreset.id : createLocalPromptPresetId();
  const nextPreset = currentPromptDraft({ id, name });
  localPromptPresets = isUpdate
    ? localPromptPresets.map((preset) => (preset.id === id ? nextPreset : preset))
    : [...localPromptPresets, nextPreset];
  persistLocalPromptPresets();
  applyPromptPresetById(id);
}

function updatePromptShareNote() {
  promptShareNote.textContent = sharePromptOnServer.checked
    ? "Uloží se na serveru a bude dostupný ostatním."
    : "Uloží se jen v tomto prohlížeči.";
}

function createLocalPromptPresetId() {
  const randomPart = Math.random().toString(36).slice(2, 8);
  return `${LOCAL_PROMPT_PREFIX}${Date.now().toString(36)}-${randomPart}`;
}

function getBrowserOwnerId() {
  let ownerId = "";
  try {
    ownerId = localStorage.getItem(BROWSER_OWNER_ID_STORAGE_KEY) || "";
  } catch {
    ownerId = "";
  }
  if (!ownerId) {
    ownerId = generateBrowserOwnerId();
    try {
      localStorage.setItem(BROWSER_OWNER_ID_STORAGE_KEY, ownerId);
    } catch {
      // localStorage may be unavailable; fall back to an in-memory id for this session.
    }
  }
  return ownerId;
}

function generateBrowserOwnerId() {
  if (window.crypto?.randomUUID) {
    return `owner-${window.crypto.randomUUID()}`;
  }
  const randomPart = Math.random().toString(36).slice(2, 10);
  return `owner-${Date.now().toString(36)}-${randomPart}`;
}

function isOwnedServerPromptPreset(presetId) {
  if (!isServerPromptPreset(presetId)) {
    return false;
  }
  const preset = promptPresets.find((item) => item.id === presetId);
  return Boolean(preset?.owner_id) && preset.owner_id === getBrowserOwnerId();
}

function loadLocalPromptPresets() {
  try {
    const raw = JSON.parse(localStorage.getItem(LOCAL_PROMPT_PRESETS_STORAGE_KEY) || "[]");
    return Array.isArray(raw) ? raw.map(normalizeLocalPromptPreset).filter(Boolean) : [];
  } catch {
    return [];
  }
}

function normalizeLocalPromptPreset(item) {
  if (!item || typeof item !== "object") {
    return null;
  }
  const id = String(item.id || "");
  const name = String(item.name || "").trim();
  if (!id.startsWith(LOCAL_PROMPT_PREFIX) || !name) {
    return null;
  }
  return {
    id,
    name,
    wp_id: String(item.wp_id || appSettings.default_wp || ""),
    system_prompt: String(item.system_prompt || ""),
    user_prompt_template: String(item.user_prompt_template || ""),
    // Inline placeholder defs are passed through as-is; the inline def editor
    // (14d) mutates them and persists via persistLocalPromptPresets().
    placeholders: item.placeholders && typeof item.placeholders === "object" && !Array.isArray(item.placeholders)
      ? item.placeholders
      : {},
  };
}

function persistLocalPromptPresets() {
  localStorage.setItem(LOCAL_PROMPT_PRESETS_STORAGE_KEY, JSON.stringify(localPromptPresets));
}

function createBlankPromptDraft() {
  activePromptPresetId = defaultPromptPresetId();
  systemPrompt.value = "";
  userPromptTemplate.value = "";
  renderPlaceholderControls();
  updatePromptTemplateWarning();
  renderPromptPresets(defaultPromptPresetId());
  systemPrompt.focus();
}

function resetPromptEditors() {
  resetPromptEditorValues();
  renderPromptPresets(defaultPromptPresetId());
}

function resetPromptEditorValues() {
  activePromptPresetId = defaultPromptPresetId();
  const defaultPrompt = getPromptPresetById(defaultPromptPresetId());
  if (defaultPrompt) {
    systemPrompt.value = defaultPrompt.system_prompt || "";
    userPromptTemplate.value = defaultPrompt.user_prompt_template || "";
    renderPlaceholderControls();
    updatePromptTemplateWarning();
  }
}

async function deleteSelectedPromptPreset() {
  if (isLocalPromptPreset(promptPreset.value)) {
    localPromptPresets = localPromptPresets.filter((preset) => preset.id !== promptPreset.value);
    persistLocalPromptPresets();
    resetPromptEditors();
    return;
  }
  if (!isServerPromptPreset(promptPreset.value)) {
    return;
  }
  const params = new URLSearchParams({ owner_id: getBrowserOwnerId() });
  const adminPassword = llmUnlockPassword.value.trim();
  if (adminPassword) {
    params.set("admin_password", adminPassword);
  }
  const response = await fetch(
    `prompt-presets/${encodeURIComponent(promptPreset.value)}?${params.toString()}`,
    { method: "DELETE" },
  );
  if (!response.ok && response.status !== 404) {
    const data = await safeJson(response);
    throw new Error(data.detail || "Prompt preset delete failed");
  }
  resetPromptEditors();
  await loadPromptPresets(defaultPromptPresetId());
}

// Collection options are scoped to the active WP. Each WP currently has a
// single collection, but the data model already supports several per WP.
function populateMsearchCollections(currentCollection) {
  const collections = getWpConfig(activeWpId)?.collections || [];
  const aiUfalSelected = isAiUfalBaseUrl(currentProviderBaseUrl());
  msearchCollection.innerHTML = collections
    .map((collection) => {
      const value = collection.msearch_collection_id || "";
      const label = collection.label || value;
      const disabled = value === WP2_MSEARCH_COLLECTION && !aiUfalSelected ? " disabled" : "";
      return `<option value="${escapeHtml(value)}"${disabled}>${escapeHtml(label)}</option>`;
    })
    .join("");
  const options = Array.from(msearchCollection.options);
  const enabledCurrent = options.find((option) => option.value === currentCollection && !option.disabled);
  const firstEnabled = options.find((option) => !option.disabled);
  msearchCollection.value = enabledCurrent?.value || firstEnabled?.value || options[0]?.value || "";
}

function updateRetrievalControls({ resetValues = false } = {}) {
  const isMsearch = retrievalBackend.value === "msearch";
  if (resetValues) {
    if (isMsearch) {
      topK.value = appSettings.msearch_defaults?.max_results ?? 10;
      msearchMode.value = appSettings.msearch_defaults?.mode || "hybrid";
      msearchMinConfidence.value = appSettings.msearch_defaults?.min_confidence ?? "";
      populateMsearchCollections(msearchCollection.value || wpDefaultCollectionMsearchId(getWpConfig(activeWpId)));
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
    element.classList.toggle("is-hidden", !isMsearch);
    element.hidden = !isMsearch;
  }
  for (const element of document.querySelectorAll(".local-control")) {
    element.classList.toggle("is-hidden", isMsearch);
    element.hidden = isMsearch;
  }
  const embeddingField = embeddingModel.closest(".field");
  if (embeddingField) {
    embeddingField.classList.toggle("is-hidden", isMsearch);
    embeddingField.hidden = isMsearch;
  }
}

function updateWeightLabels() {
  denseWeightValue.value = Number(denseWeight.value).toFixed(2);
  bm25WeightValue.value = Number(bm25Weight.value).toFixed(2);
}

function updateRerankControls() {
  rerankField.hidden = !rerankAvailable;
  rerankCandidatesField.hidden = !rerankAvailable;
  rerankWeightValue.value = Number(rerankWeight.value).toFixed(1);
  rerankNote.hidden = !rerankAvailable || Number(rerankWeight.value) <= 0;
}

rerankWeight.addEventListener("input", updateRerankControls);

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

function updateLlmPolicyNote(policy, unlocked = false, browserApiKeyProvided = false) {
  if (!llmPolicyNote) {
    return;
  }
  const provider = selectedProviderConfig();
  const providerLabel = provider.label || provider.id || "vybraného poskytovatele";
  if (browserApiKeyProvided) {
    llmPolicyNote.textContent = `Vlastní API klíč přepisuje uložený klíč pro ${providerLabel}. Při odeslání se ověří, že klíč patří k vybranému poskytovateli.`;
    return;
  }
  if (unlocked) {
    llmPolicyNote.textContent = `Odemčeno: v rozbalovacím seznamu jsou modely pro ${providerLabel} a lze zadat i jiný model.`;
    return;
  }
  const publicModels = providerPublicModels(provider, appSettings);
  if (publicModels.length > 0) {
    llmPolicyNote.textContent = `Bez odemykacího hesla jsou pro ${providerLabel} dostupné aktuálně načtené veřejné modely: ${publicModels.join(", ")}.`;
    return;
  }
  llmPolicyNote.textContent = `Pro ${providerLabel} zadej API klíč v Nastavení, nebo nastav veřejné modely v .env.`;
}

function nullableNumber(value) {
  if (value === "") {
    return null;
  }
  return Number(value);
}

function formatErrorDetail(detail) {
  if (!detail || typeof detail === "string") {
    return detail || "Request failed";
  }
  if (typeof detail === "object" && detail.message) {
    return String(detail.message);
  }
  return JSON.stringify(detail);
}

function nullableInteger(value) {
  if (value === "") {
    return null;
  }
  return Number.parseInt(value, 10);
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
  renderBudgetNotes(sourcesEl, currentBudgetWarnings, currentOmittedChunks, currentTokenBudget, currentConversationSummary);
  renderBaselineComparison();
}

function renderBaselineComparison() {
  const hasBaseline = Array.isArray(currentBaselineChunks) && currentBaselineChunks.length > 0;
  toggleBaselineBtn.hidden = !hasBaseline;
  if (!hasBaseline) {
    baselineVisible = false;
  }
  const show = hasBaseline && baselineVisible;
  baselineColumnEl.hidden = !show;
  rerankedColumnTitleEl.hidden = !show;
  toggleBaselineBtn.setAttribute("aria-expanded", show ? "true" : "false");
  toggleBaselineBtn.textContent = show
    ? "Skrýt pořadí bez re-rankingu"
    : "Porovnat s pořadím bez re-rankingu";
  if (show) {
    const baselineSources = chunksToSources(currentBaselineChunks);
    renderSourceCards(baselineSourcesEl, baselineSources, currentBaselineChunks, question.value, new Set(), "baseline-source");
  } else {
    baselineSourcesEl.innerHTML = "";
  }
}

toggleBaselineBtn.addEventListener("click", () => {
  baselineVisible = !baselineVisible;
  renderBaselineComparison();
});

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
      const budgetStatus = chunk?.metadata?.budget_status || "";
      const trimmedBadge = budgetStatus === "trimmed" ? `<span class="source-badge">zkráceno pro prompt</span>` : "";
      const originalText = chunk?.metadata?.original_text || "";
      return `
        <article class="source${usedClass}" id="${escapeHtml(idPrefix)}-${escapeHtml(citationId)}" data-citation-id="${escapeHtml(citationId)}">
          <strong>[${escapeHtml(citationId)}] ${title} ${trimmedBadge}</strong>
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
          ${
            originalText
              ? `<details class="chunk-details">
                  <summary>Původní nalezený úryvek</summary>
                  <p class="full-chunk">${highlightText(originalText, highlightTerms)}</p>
                </details>`
              : ""
          }
        </article>
      `;
    })
    .join("");
}

function renderBudgetNotes(container, warnings = [], omittedChunks = [], tokenBudget = null, conversationSummary = "") {
  const parts = [];
  if (warnings.length) {
    parts.push(`
      <div class="budget-note">
        ${warnings.map((warning) => `<p>${escapeHtml(warning)}</p>`).join("")}
      </div>
    `);
  }
  if (tokenBudget) {
    parts.push(`
      <details class="budget-details">
        <summary>Tokenový rozpočet</summary>
        <p>Prompt bez zdrojů: ${escapeHtml(tokenBudget.estimated_non_source_tokens ?? "?")} tokenů · zdroje: ${escapeHtml(tokenBudget.estimated_source_tokens ?? "?")} · rezerva odpovědi: ${escapeHtml(tokenBudget.reserved_output_tokens ?? "?")} · window: ${escapeHtml(tokenBudget.context_window_tokens ?? "?")}</p>
      </details>
    `);
  }
  if (conversationSummary) {
    parts.push(`
      <details class="budget-details">
        <summary>Komprimovaný kontext konverzace</summary>
        <p>${escapeHtml(conversationSummary)}</p>
      </details>
    `);
  }
  if (omittedChunks.length) {
    parts.push(`
      <details class="budget-details">
        <summary>Neposlané nalezené chunky (${omittedChunks.length})</summary>
        ${omittedChunks
          .map((chunk) => {
            const title = chunk.metadata?.title || chunk.metadata?.source_path || "Neznámý dokument";
            return `<p><strong>[${escapeHtml(chunk.citation_id)}] ${escapeHtml(title)}</strong><br>${escapeHtml(shortenText(chunk.text || "", 320))}</p>`;
          })
          .join("")}
      </details>
    `);
  }
  if (parts.length) {
    container.insertAdjacentHTML("afterbegin", parts.join(""));
  }
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
	    conversation_summary: "",
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
  const budgetWarnings =
    message.role === "assistant" && message.chunk_budget_warnings?.length
      ? `<div class="budget-note conversation-budget-note">${message.chunk_budget_warnings
          .map((warning) => `<p>${escapeHtml(warning)}</p>`)
          .join("")}</div>`
      : "";
  const contextStatus = message.role === "assistant" ? renderConversationContextStatus(message) : "";
  return `
    <article class="conversation-message ${messageClass}">
      <div class="conversation-message-label">${roleLabel}</div>
      <div class="conversation-message-body">${body}</div>
      ${budgetWarnings}
      ${contextStatus}
      ${metaParts.length ? `<div class="conversation-message-meta">${metaParts.join(" · ")}</div>` : ""}
    </article>
  `;
}

function renderConversationContextStatus(message) {
  const budget = message.token_budget;
  const summary = message.conversation_summary || "";
  if (!budget && !summary) {
    return "";
  }

  const usedChunks = Number(budget?.used_chunk_count ?? 0);
  const omittedChunks = Number(budget?.omitted_chunk_count ?? 0);
  const trimmedChunks = Number(budget?.trimmed_chunk_count ?? 0);
  const totalChunks = usedChunks + omittedChunks;
  const sourceText =
    totalChunks > 0
      ? `${usedChunks}/${totalChunks} chunků posláno`
      : budget
        ? "bez zdrojových chunků"
        : "stav kontextu";
  const compressionText = budget?.conversation_summary_used || summary ? "komprese zapnutá" : "bez komprese";
  const visibleParts = [sourceText, compressionText];
  if (trimmedChunks > 0) {
    visibleParts.push(`${trimmedChunks} zkráceno`);
  }
  const totalInputTokens =
    budget?.estimated_total_input_tokens ??
    (budget ? Number(budget.estimated_non_source_tokens ?? 0) + Number(budget.estimated_source_tokens ?? 0) : null);
  const usedWindowTokens =
    budget && totalInputTokens !== null
      ? totalInputTokens + Number(budget.reserved_output_tokens ?? 0)
      : null;
  const usagePercent =
    budget?.context_window_tokens && usedWindowTokens !== null
      ? Math.max(0, Math.min(100, Math.round((usedWindowTokens / Number(budget.context_window_tokens)) * 100)))
      : null;
  if (totalInputTokens !== null) {
    visibleParts.unshift(`${totalInputTokens} tokenů vstup`);
  }

  const detailRows = budget
    ? [
        ["Context window", budget.context_window_tokens],
        ["Celkem vstup", totalInputTokens],
        ["Použitelný vstup po rezervě", budget.usable_input_tokens],
        ["Prompt bez zdrojů", budget.estimated_non_source_tokens],
        ["Historie konverzace", budget.estimated_conversation_history_tokens ?? 0],
        ["Zdroje poslané modelu", budget.estimated_source_tokens],
        ["Rezerva pro odpověď", budget.reserved_output_tokens],
        ["Využití okna včetně rezervy", usagePercent === null ? null : `${usagePercent}%`],
        ["Použité chunky", usedChunks],
        ["Vynechané chunky", omittedChunks],
        ["Zkrácené chunky", trimmedChunks],
        ["Komprese konverzace", budget.conversation_summary_used || summary ? "ano" : "ne"],
      ]
    : [["Komprese konverzace", "ano"]];
  const detailTable = detailRows
    .map(
      ([label, value]) => `
        <div class="context-budget-row">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value ?? "?")}</strong>
        </div>
      `,
    )
    .join("");
  const summaryBlock = summary
    ? `
      <div class="context-summary-block">
        <h4>Komprimovaný kontext konverzace</h4>
        <p>${escapeHtml(summary)}</p>
      </div>
    `
    : "";

  return `
    <div class="conversation-context-status">
      <div class="conversation-context-line">
        ${
          usagePercent === null
            ? `<span>Kontext</span>`
            : `<span class="context-usage-ring" style="--context-used: ${escapeHtml(usagePercent)}%"><span>${escapeHtml(usagePercent)}%</span></span>`
        }
        <strong>${visibleParts.map((part) => escapeHtml(part)).join(" · ")}</strong>
      </div>
      <details class="budget-details conversation-context-details">
        <summary>Detail kontextového okna</summary>
        <div class="context-budget-grid">${detailTable}</div>
        ${summaryBlock}
      </details>
    </div>
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
    conversation_summary: conversation.conversation_summary || null,
    conversation_history: conversation.messages.map((message) => ({
      role: message.role,
      content: message.content,
    })),
  });
  const sanitizedPayload = sanitizeHistorySettings(payload);

  try {
    await chatRequest(payload, {
      onSources(data) {
        latestChunks = data.retrieved_chunks || [];
        latestSources = data.sources || chunksToSources(latestChunks);
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
            settings: sanitizedPayload,
            sources: latestSources,
            retrieved_chunks: latestChunks,
            omitted_chunks: [],
            token_budget: null,
            chunk_budget_warnings: [],
            conversation_summary: liveConversation.conversation_summary || null,
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
            settings: sanitizedPayload,
            sources: latestSources,
            retrieved_chunks: latestChunks,
            omitted_chunks: [],
            token_budget: null,
            chunk_budget_warnings: [],
            conversation_summary: liveConversation.conversation_summary || null,
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
          settings: sanitizedPayload,
          sources: data.sources || latestSources,
          retrieved_chunks: data.retrieved_chunks || latestChunks,
          omitted_chunks: data.omitted_chunks || [],
          token_budget: data.token_budget || null,
          chunk_budget_warnings: data.chunk_budget_warnings || [],
          conversation_summary: data.conversation_summary || null,
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
        updateConversation({
          ...liveConversation,
          conversation_summary: data.conversation_summary || liveConversation.conversation_summary || "",
          updatedAt: new Date().toISOString(),
          messages,
        });
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
          settings: sanitizedPayload,
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
    omitted_chunks: entry.omitted_chunks || [],
    token_budget: entry.token_budget || null,
    chunk_budget_warnings: entry.chunk_budget_warnings || [],
    conversation_summary: entry.conversation_summary || null,
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
  delete sanitized.admin_password;
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

// Re-ranking countdown: each batch event re-anchors a deadline, and a ticking
// interval renders the remaining time between batches so the ETA visibly counts
// down instead of only jumping when a batch lands.
let rerankCountdownTimer = null;
let rerankEtaDeadline = null; // performance.now() ms when ETA hits zero, or null
let rerankCounted = ""; // last "done/total" text, kept while only the clock ticks

function renderRerankCountdown() {
  let etaText = "";
  if (rerankEtaDeadline !== null) {
    const remaining = Math.max(0, (rerankEtaDeadline - performance.now()) / 1000);
    etaText = remaining > 0.05 ? ` · ~${remaining.toFixed(1)}s` : " · dokončuji…";
  }
  rerankProgressLabel.textContent = `Re-ranking${rerankCounted}${etaText}`;
}

function onRerankProgressUpdate(progress) {
  rerankProgressEl.hidden = false;
  if (progress.total) {
    rerankCounted = ` ${progress.done}/${progress.total}`;
    rerankProgressFill.style.width = `${Math.round((progress.done / progress.total) * 100)}%`;
  }
  // Re-anchor the countdown from the freshly observed ETA (self-correcting).
  rerankEtaDeadline = typeof progress.eta_seconds === "number" ? performance.now() + progress.eta_seconds * 1000 : null;
  renderRerankCountdown();
  if (rerankCountdownTimer === null) {
    rerankCountdownTimer = window.setInterval(renderRerankCountdown, 100);
  }
}

function stopRerankCountdown() {
  if (rerankCountdownTimer !== null) {
    window.clearInterval(rerankCountdownTimer);
    rerankCountdownTimer = null;
  }
  rerankEtaDeadline = null;
  rerankCounted = "";
  rerankProgressEl.hidden = true;
  rerankProgressFill.style.width = "0";
}

function formatTimingLabel(doneData, modelLabel) {
  // Total time, with a per-stage breakdown (rerank only when it ran, generation
  // always) so the user can see where the wall time went.
  const parts = [];
  if (typeof doneData.rerank_time_seconds === "number") {
    parts.push(`re-ranking ${doneData.rerank_time_seconds.toFixed(1)}s`);
  }
  if (typeof doneData.generation_time_seconds === "number") {
    parts.push(`generování ${doneData.generation_time_seconds.toFixed(1)}s`);
  }
  let label = `Hotovo za ${doneData.response_time_seconds}s`;
  if (parts.length) {
    label += ` (${parts.join(" · ")})`;
  }
  if (modelLabel) {
    label += ` · ${modelLabel}`;
  }
  return label;
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
  const omittedChunks = entry.omitted_chunks || [];
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
        ${renderSetting("WP", wpLabelFromSettings(entry.settings))}
        ${renderSetting("Prompt", promptPresetLabelFromSettings(entry.settings))}
        ${renderPlaceholderSettings(entry.settings)}
        ${renderSetting("Poskytovatel", entry.settings?.llm_provider)}
        ${renderSetting("Model", formatModelUsageLabel(entry.model_used || entry.settings?.model, entry.upstream_model))}
        ${renderSetting("LLM endpoint", entry.settings?.llm_base_url)}
        ${renderSetting("Pouze zdroje", entry.mode === "retrieve" ? "ano" : "ne")}
	        ${renderSetting("Top-k", entry.settings?.top_k)}
	        ${renderSetting("Context window", entry.token_budget?.context_window_tokens || entry.settings?.context_window_tokens)}
	        ${renderSetting("Tokenů ve zdrojích", entry.token_budget?.estimated_source_tokens)}
	        ${renderSetting("Váha embeddingů", entry.settings?.dense_weight)}
        ${renderSetting("Váha BM25", entry.settings?.bm25_weight)}
        ${renderSetting("Min. confidence mSearch", entry.settings?.msearch_min_confidence)}
        ${renderSetting("Min. skóre", entry.settings?.min_score)}
        ${renderSetting("Min. vůči nejlepšímu", entry.settings?.min_relative_score)}
        ${renderSetting("Doba odpovědi", entry.response_time_seconds ? `${entry.response_time_seconds}s` : null)}
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
	  renderBudgetNotes(
	    historySources,
	    entry.chunk_budget_warnings || [],
	    omittedChunks,
	    entry.token_budget || null,
	    entry.conversation_summary || "",
	  );
	}

function renderSetting(label, value) {
  const displayValue = label === "Poskytovatel" ? providerLabelForId(value) : value;
  return `
    <div class="setting-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(displayValue ?? "—")}</strong>
    </div>
  `;
}

// Render one setting card per saved placeholder selection, labeled by the def
// (and, for selects, the chosen option's label). Defs come from the entry's saved
// inline `placeholder_defs` overlaid on the current merged globals.
function renderPlaceholderSettings(settings) {
  const selections = settings?.selections && typeof settings.selections === "object" ? settings.selections : {};
  const inline = settings?.placeholder_defs && typeof settings.placeholder_defs === "object" ? settings.placeholder_defs : {};
  const globals = globalPlaceholderDefs();
  return Object.entries(selections)
    .map(([name, value]) => {
      const def = inline[name] || globals[name] || null;
      const label = def?.label || name;
      let display = value;
      if (def?.kind === "select") {
        const option = (Array.isArray(def.options) ? def.options : []).find((item) => item.name === value);
        display = option?.label || value;
      } else if (def?.kind === "text") {
        display = String(value || "").trim() || "žádné";
      }
      return renderSetting(label, display);
    })
    .join("");
}

function promptPresetLabelFromSettings(settings) {
  const presetId = promptPresetIdFromSettings(settings);
  const preset = getPromptPresetById(presetId);
  return settings?.prompt_preset_name || preset?.name || presetId;
}

function wpLabelFromSettings(settings) {
  const wp = getWpConfig(resolveWpId(settings?.wp_id));
  return wp?.label || settings?.wp_id || "";
}

function promptPresetIdFromSettings(settings) {
  const savedId = settings?.prompt_preset_id;
  if (promptPresetExists(savedId)) {
    return normalizePromptPresetId(savedId);
  }
  // Legacy history used builtin-<style> ids; map them to the matching WP1 built-in.
  const style = String(settings?.style || savedId || "").replace(BUILTIN_PROMPT_PREFIX, "");
  const legacyId = `wp1-${style}`;
  if (promptPresetExists(legacyId)) {
    return legacyId;
  }
  return defaultPromptPresetId(resolveWpId(settings?.wp_id));
}

function applyHistoryEntryToForm(entry) {
  question.value = entry.question || "";
  const providerValue = normalizeProviderId(entry.settings?.llm_provider || llmProvider.value || "");
  if (providerValue) {
    loadProviderValues(providerValue, { preferStored: true });
  }
  activeWpId = resolveWpId(entry.settings?.wp_id);
  wpSelect.value = activeWpId;
  populateMsearchCollections(entry.settings?.msearch_collection || wpDefaultCollectionMsearchId(getWpConfig(activeWpId)));
  const savedPromptId = promptPresetIdFromSettings(entry.settings || {});
  if (promptPresetExists(savedPromptId)) {
    // Re-selects the prompt and re-renders controls reset to the prompt defaults.
    applyPromptPresetById(savedPromptId);
  } else {
    renderPromptPresets(defaultPromptPresetId());
  }
  // Re-apply any saved prompt-text overrides, which can change the active tokens,
  // then re-render controls before restoring the saved selection values.
  systemPrompt.value = entry.settings?.system_prompt || systemPrompt.value;
  userPromptTemplate.value = entry.settings?.user_prompt_template || userPromptTemplate.value;
  renderPlaceholderControls();
  applyPlaceholderSelections(entry.settings?.selections);
  updatePromptTemplateWarning();
  refreshModelOptions(appSettings);
  const modelValue = entry.settings?.model || "";
  const unlocked = customModelAllowed();
  if (modelValue && Array.from(model.options).some((option) => option.value === modelValue)) {
    model.value = modelValue;
  } else if (unlocked && modelValue) {
    customModel.value = modelValue;
    model.value = CUSTOM_MODEL_VALUE;
  } else if (model.options.length > 0) {
    model.value = model.options[0].value;
  }
  updateCustomModelVisibility(unlocked);
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
