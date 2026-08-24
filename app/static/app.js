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
const logoutAdminButton = document.querySelector("#logoutAdminButton");
const toggleUnlockPasswordButton = document.querySelector("#toggleUnlockPasswordButton");
const unlockModelsStatus = document.querySelector("#unlockModelsStatus");
const refreshModelsButton = document.querySelector("#refreshModelsButton");
const modelRefreshStatus = document.querySelector("#modelRefreshStatus");
const mainContextWindowTokens = document.querySelector("#mainContextWindowTokens");
const modelContextWindowNote = document.querySelector("#modelContextWindowNote");
const reasoningEffortField = document.querySelector("#reasoningEffortField");
const reasoningEffort = document.querySelector("#reasoningEffort");
const reasoningPanel = document.querySelector("#reasoningPanel");
const reasoningText = document.querySelector("#reasoningText");
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
const retrieveButton = document.querySelector("#retrieveButton");
const queryTransformSection = document.querySelector("#queryTransformSection");
const queryTransformApplyToggle = document.querySelector("#queryTransformApplyToggle");
const queryTransformRowsEl = document.querySelector("#queryTransformRows");
const appliedQueryTransformNote = document.querySelector("#appliedQueryTransformNote");
const predefinedQuestionWrap = document.querySelector("#predefinedQuestionWrap");
const predefinedQuestionButton = document.querySelector("#predefinedQuestionButton");
const predefinedQuestionList = document.querySelector("#predefinedQuestionList");
const msearchCollection = document.querySelector("#msearchCollection");
const msearchMinConfidence = document.querySelector("#msearchMinConfidence");
const msearchMinConfidenceValue = document.querySelector("#msearchMinConfidenceValue");
const wpSelect = document.querySelector("#wpSelect");
const settingsWpSelect = document.querySelector("#settingsWpSelect");
const activePromptPreset = document.querySelector("#activePromptPreset");
const promptPreset = document.querySelector("#promptPreset");
const newPromptButton = document.querySelector("#newPromptButton");
const savePromptAsButton = document.querySelector("#savePromptAsButton");
const sharePromptOnServer = document.querySelector("#sharePromptOnServer");
const promptShareNote = document.querySelector("#promptShareNote");
const promptPresetStatus = document.querySelector("#promptPresetStatus");
const updatePromptButton = document.querySelector("#updatePromptButton");
const deletePromptButton = document.querySelector("#deletePromptButton");
const llmPolicyNote = document.querySelector("#llmPolicyNote");
const promptName = document.querySelector("#promptName");
const promptNote = document.querySelector("#promptNote");
const systemPrompt = document.querySelector("#systemPrompt");
const userPromptTemplate = document.querySelector("#userPromptTemplate");
const promptTemplateWarning = document.querySelector("#promptTemplateWarning");
const globalPlaceholderDefsList = document.querySelector("#globalPlaceholderDefsList");
const globalPlaceholderDefsStatus = document.querySelector("#globalPlaceholderDefsStatus");
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
const placeholderDefShareField = document.querySelector("#placeholderDefShareField");
const placeholderDefShareOnServer = document.querySelector("#placeholderDefShareOnServer");
const placeholderDefShareNote = document.querySelector("#placeholderDefShareNote");
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
const queryTransformEnabledToggle = document.querySelector("#queryTransformEnabledToggle");
const queryTransformAutoApplyToggle = document.querySelector("#queryTransformAutoApplyToggle");
const queryTransformDisabledNote = document.querySelector("#queryTransformDisabledNote");
const queryTransformSettingsBody = document.querySelector("#queryTransformSettingsBody");
const queryTransformActionDefsList = document.querySelector("#queryTransformActionDefsList");
const newQueryTransformActionButton = document.querySelector("#newQueryTransformActionButton");
const resetBuiltinQueryTransformButton = document.querySelector("#resetBuiltinQueryTransformButton");
const queryTransformActionDialog = document.querySelector("#queryTransformActionDialog");
const queryTransformActionTitle = document.querySelector("#queryTransformActionTitle");
const closeQueryTransformActionButton = document.querySelector("#closeQueryTransformActionButton");
const queryTransformActionType = document.querySelector("#queryTransformActionType");
const queryTransformActionId = document.querySelector("#queryTransformActionId");
const queryTransformActionLabelInput = document.querySelector("#queryTransformActionLabel");
const queryTransformActionDescription = document.querySelector("#queryTransformActionDescription");
const queryTransformActionLindatFields = document.querySelector("#queryTransformActionLindatFields");
const queryTransformActionSourceLang = document.querySelector("#queryTransformActionSourceLang");
const queryTransformActionTargetLang = document.querySelector("#queryTransformActionTargetLang");
const queryTransformActionModel = document.querySelector("#queryTransformActionModel");
const queryTransformActionLlmFields = document.querySelector("#queryTransformActionLlmFields");
const queryTransformActionPrompt = document.querySelector("#queryTransformActionPrompt");
const queryTransformActionUseForAnswer = document.querySelector("#queryTransformActionUseForAnswer");
const queryTransformActionError = document.querySelector("#queryTransformActionError");
const deleteQueryTransformActionButton = document.querySelector("#deleteQueryTransformActionButton");
const saveQueryTransformActionButton = document.querySelector("#saveQueryTransformActionButton");
const topK = document.querySelector("#topK");
const topKValue = document.querySelector("#topKValue");
const msearchRescore = document.querySelector("#msearchRescore");
const msearchRescoreNote = document.querySelector("#msearchRescoreNote");
const rescoreThresholdNote = document.querySelector("#rescoreThresholdNote");
const minRelativeScore = document.querySelector("#minRelativeScore");
const minRelativeScoreValue = document.querySelector("#minRelativeScoreValue");
const submitButton = document.querySelector("#submitButton");
const cancelButton = document.querySelector("#cancelButton");
const randomQuestionButton = document.querySelector("#randomQuestionButton");
const statusEl = document.querySelector("#status");
const loadingIndicator = document.querySelector("#loadingIndicator");
const rerankProgressEl = document.querySelector("#rerankProgress");
const rerankProgressFill = document.querySelector("#rerankProgressFill");
const rerankProgressLabel = document.querySelector("#rerankProgressLabel");
const answerEl = document.querySelector("#answer");
const answerQuestionInfo = document.querySelector("#answerQuestionInfo");
const answerQuestionText = document.querySelector("#answerQuestionText");
const sourcesEl = document.querySelector("#sources");
const answerActions = document.querySelector("#answerActions");
const copyAnswerStatus = document.querySelector("#copyAnswerStatus");
const retrievalQueryInfo = document.querySelector("#retrievalQueryInfo");
const retrievalQueryText = document.querySelector("#retrievalQueryText");
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
const historyTabMine = document.querySelector("#historyTabMine");
const historyTabShared = document.querySelector("#historyTabShared");
const historyAuthorName = document.querySelector("#historyAuthorName");
const historyAuthorNameLabel = document.querySelector("#historyAuthorNameLabel");
const historyShareStatus = document.querySelector("#historyShareStatus");
const shareSelectedButton = document.querySelector("#shareSelectedButton");
const conversationDialog = document.querySelector("#conversationDialog");
const conversationList = document.querySelector("#conversationList");
const conversationMeta = document.querySelector("#conversationMeta");
const conversationMessages = document.querySelector("#conversationMessages");
const conversationSources = document.querySelector("#conversationSources");
const conversationRetrievalInfo = document.querySelector("#conversationRetrievalInfo");
const conversationRewriteQuery = document.querySelector("#conversationRewriteQuery");
const conversationForm = document.querySelector("#conversationForm");
const conversationQuestion = document.querySelector("#conversationQuestion");
const conversationSubmitButton = document.querySelector("#conversationSubmitButton");
const conversationCancelButton = document.querySelector("#conversationCancelButton");
const conversationRequestStatus = document.querySelector("#conversationRequestStatus");
const conversationStorageStatus = document.querySelector("#conversationStorageStatus");
const conversationStorageStatusText = document.querySelector("#conversationStorageStatusText");
const legacyHistoryStorageActions = document.querySelector("#legacyHistoryStorageActions");
const exportLegacyHistoryButton = document.querySelector("#exportLegacyHistoryButton");
const deleteLegacyHistoryButton = document.querySelector("#deleteLegacyHistoryButton");
const newConversationButton = document.querySelector("#newConversationButton");
const deleteConversationButton = document.querySelector("#deleteConversationButton");
const closeConversationButton = document.querySelector("#closeConversationButton");
const convWpSelect = document.querySelector("#convWpSelect");
const convPromptSelect = document.querySelector("#convPromptSelect");
const convProvider = document.querySelector("#convProvider");
const convModel = document.querySelector("#convModel");
const convCustomModelField = document.querySelector("#convCustomModelField");
const convCustomModel = document.querySelector("#convCustomModel");
const convContextWindowTokens = document.querySelector("#convContextWindowTokens");
const convModelContextWindowNote = document.querySelector("#convModelContextWindowNote");
const convPlaceholderControls = document.querySelector("#convPlaceholderControls");
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
// fields. The old key is not loaded into the current view; conversation mode
// offers an explicit export-before-delete action when it still occupies space.
const HISTORY_STORAGE_KEY = "czdemos4ai-history-v2";
const LEGACY_HISTORY_STORAGE_KEY = "czdemos4ai-history";
// Display name attached to items this browser shares to /shared-history.
const AUTHOR_NAME_STORAGE_KEY = "czdemos4ai-author-name";
const CONVERSATION_STORAGE_KEY = "czdemos4ai-conversations";
const LLM_SETTINGS_STORAGE_KEY = "czdemos4ai-llm-settings";
const TOKEN_BUDGET_STORAGE_KEY = "czdemos4ai-token-budget";
const LOCAL_PROMPT_PRESETS_STORAGE_KEY = "czdemos4ai-local-prompt-presets";
// Browser-local global placeholder defs (name -> def). Private to this browser,
// no password. In resolution they sit between inline (on the selected prompt) and
// the shared server overlay: inline -> browser-local -> shared overlay -> code floor.
const LOCAL_PLACEHOLDER_DEFS_STORAGE_KEY = "czdemos4ai-local-placeholder-defs";
const BROWSER_OWNER_ID_STORAGE_KEY = "czdemos4ai-browser-owner-id";
const ANALYTICS_SESSION_ID_STORAGE_KEY = "czdemos4ai-analytics-session-id";
const nativeFetch = window.fetch.bind(window);

function newAnalyticsId() {
  return globalThis.crypto?.randomUUID?.()
    || `fallback-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function analyticsSessionId() {
  let value = sessionStorage.getItem(ANALYTICS_SESSION_ID_STORAGE_KEY);
  if (!value) {
    value = newAnalyticsId();
    sessionStorage.setItem(ANALYTICS_SESSION_ID_STORAGE_KEY, value);
  }
  return value;
}

window.fetch = function analyticsFetch(input, init = {}) {
  const url = new URL(typeof input === "string" ? input : input.url, window.location.href);
  if (url.origin !== window.location.origin) {
    return nativeFetch(input, init);
  }
  const { analyticsTurnId = null, analyticsAppOpen = false, ...fetchInit } = init;
  const headers = new Headers(fetchInit.headers || (input instanceof Request ? input.headers : undefined));
  headers.set("X-Client-Id", getBrowserOwnerId());
  headers.set("X-Session-Id", analyticsSessionId());
  if (analyticsTurnId) {
    headers.set("X-Turn-Id", analyticsTurnId);
  }
  if (analyticsAppOpen) {
    headers.set("X-App-Open", "1");
  }
  return nativeFetch(input, { ...fetchInit, headers });
};
const CUSTOM_PROVIDER_ID = "custom";
const DEFAULT_CUSTOM_PROVIDER_LABEL = "Custom provider";
const LEGACY_DEFAULT_PROMPT_PRESET_ID = "default";
const BUILTIN_PROMPT_PREFIX = "builtin-";
const LOCAL_PROMPT_PREFIX = "local-";
const MAX_STORED_HISTORY_ENTRIES = 40;
const COMPACT_STORED_CHUNK_TEXT_LIMIT = 1200;
// System placeholders are filled by the server and never warned about; the two
// parameter placeholders shipped in the code floor (length, custom_instructions)
// are also "known" so they do not trigger the unknown-variable warning.
const KNOWN_PROMPT_VARIABLES = new Set([
  "question",
  "retrieved_snippets",
  "current_date",
  "length",
  "custom_instructions",
]);
const CODE_FLOOR_PLACEHOLDERS = new Set(["length", "custom_instructions"]);
const SAVE_PROMPT_BEFORE_VARIABLES_MESSAGE = "Nejdřív ulož prompt jako nový. Abys mohl přidat nové proměnné.";
const SAVE_PROMPT_BEFORE_QUERY_TRANSFORM_MESSAGE = "Nejdřív ulož prompt jako nový (lokálně nebo sdíleně). Pak půjde zapnout úprava dotazu.";
const UNLOCK_BUILTIN_QUERY_TRANSFORM_MESSAGE = "Transformaci vestavěného profilu může upravit administrátor. Nejdřív aktivuj admin přístup.";
const CUSTOM_MODEL_VALUE = "__custom__";

let selectedHistoryId = null;
let selectedConversationId = null;
// History dialog tab ("mine" = local localStorage, "shared" = server) plus the
// state backing the Shared tab and the local multi-select-to-share flow.
let activeHistoryTab = "mine";
let selectedSharedId = null;
let sharedHistoryItems = [];
const selectedShareIds = new Set();
let streamedAnswerText = "";
let currentAnswerSources = [];
let currentRetrievedChunks = [];
let currentRetrievalQuery = "";
let currentAnswerQuestion = "";
let currentOmittedChunks = [];
let currentReasoning = "";
// Sources-panel view state (order + uncited visibility). One object per panel,
// passed into renderSourceCards rather than read from it, so the main panel,
// conversation mode and history cannot desync.
let mainSourcesView = Avatar.createSourcesView();
// null means "not decided yet" — the panel derives the settled view from the
// stored answer on first render, and keeps whatever the user toggles after that.
let conversationSourcesView = null;
// The baseline column is a rank-vs-rank comparison, so it never flips.
const STATIC_SOURCES_VIEW = Avatar.createSourcesView({ canFlip: false, complete: true });
let currentBaselineChunks = [];
let baselineVisible = false;
// Whether the last query asked mSearch to rescore server-side; drives the small
// "reordered by mSearch" note (which has no baseline comparison to show).
let currentMsearchRescoreUsed = false;
let currentBudgetWarnings = [];
let currentTokenBudget = null;
let currentConversationSummary = "";
// Source card the user clicked to light up its citation markers in the answer,
// as { scope, citationId }. Kept outside the DOM because both the answer and the
// source cards are re-rendered from scratch (on every streamed token, even), so
// the highlight has to be reapplied after each render rather than live in it.
let activeCitation = null;
let appliedQueryTransform = null;
// Per-action UI state for the inline "Upravit dotaz" rows, keyed by action id.
// Rebuilt whenever the question text or the resolved set of actions changes.
let queryTransformRowState = {};
let queryTransformRowsQuestion = null;
let queryTransformSelectedActionId = null;
let queryTransformApplyEnabled = null;
let appSettings = {};
let promptPresets = [];
let localPromptPresets = [];
let draftPromptPreset = null;
let activePromptPresetId = "";
let activeWpId = "";
// Prepared questions are static for a page load. Cache successful loads so a WP
// switch can identify whether the current text is managed without another
// request. These revisions guard asynchronous loads against stale UI updates.
const predefinedQuestionsByWp = new Map();
const predefinedQuestionLoadsByWp = new Map();
let predefinedQuestionsRenderRevision = 0;
let questionEditRevision = 0;
let managedQuestion = null;
// WP whose prompts/inline-defs the Settings dialog edits. Initialized to
// activeWpId when the dialog opens; the user can switch it inside Settings
// without touching the main page (which keeps using activeWpId).
let settingsWpId = "";
// Resolved parameter placeholder defs for the active prompt (name -> def) and the
// current control values (name -> value). Both are rebuilt on every prompt switch.
let activePlaceholderDefs = {};
let placeholderSelections = {};
// Placeholder controls render into whichever container is active: the main page
// by default, or the conversation settings bar while the conversation modal is
// open. Swapping this lets the existing prompt/placeholder machinery target the
// conversation container without duplicating it.
let activePlaceholderContainer = placeholderControls;
// While the conversation modal is open the global settings state (activeWpId,
// active prompt, provider/model, placeholder selections, ...) represents the
// ACTIVE conversation. mainSettingsBackup holds the main page's own settings so
// they can be restored verbatim when the modal closes.
let conversationSettingsActive = false;
let mainSettingsBackup = null;
// Browser-local global placeholder defs (name -> def), loaded from localStorage.
let localPlaceholderDefs = {};
let llmModelsUnlocked = false;
let contextWindowManuallyEdited = false;
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

// Query transforms belong to prompt presets. Built-in WP configuration does
// not provide a fallback.
function resolvedQueryTransformConfig() {
  const preset = getPromptPresetById(activePromptPresetId);
  const raw = preset?.query_transform;
  if (!raw || typeof raw !== "object" || raw.enabled !== true) {
    return null;
  }
  const actions = Array.isArray(raw.actions)
    ? raw.actions.filter((action) => (
      action
      && typeof action === "object"
      && String(action.id || "").trim()
      && String(action.description || "").trim()
      && ["lindat", "llm"].includes(String(action.type || "").toLowerCase())
    ))
    : [];
  return actions.length ? {
    ...raw,
    auto_apply: raw.auto_apply !== false,
    actions,
  } : null;
}

function clearAppliedQueryTransform({ refreshButton = true } = {}) {
  appliedQueryTransform = null;
  queryTransformSelectedActionId = null;
  queryTransformApplyEnabled = null;
  // Forces renderQueryTransformSection() to rebuild the rows from scratch.
  queryTransformRowsQuestion = null;
  if (refreshButton) {
    renderQueryTransformSection();
  }
}

function queryTransformRunLabel(action) {
  return String(action.type).toLowerCase() === "lindat" ? "Přeložit" : "Upravit pomocí LLM";
}

function buildQueryTransformRowsDom(config) {
  if (!queryTransformRowsEl) {
    return;
  }
  queryTransformRowsEl.innerHTML = config.actions
    .map((action) => {
      const actionId = String(action.id);
      const state = queryTransformRowState[actionId] || {};
      const isLlm = String(action.type).toLowerCase() === "llm";
      const hasInstructionField = isLlm && String(action.prompt_template || "").includes("{instruction}");
      const collapsed = Boolean(state.collapsed);
      const hasResult = Boolean(String(state.result || "").trim());
      return `
        <div class="query-transform-row${collapsed ? " is-collapsed" : ""}" data-action-row="${escapeHtml(actionId)}">
          <div class="query-transform-row-header">
            <button
              class="query-transform-row-select"
              type="button"
              data-role="select"
              title="Vybrat tuto transformaci"
              aria-label="Vybrat tuto úpravu"
            ><span class="query-transform-row-select-dot" aria-hidden="true"></span></button>
            <button class="query-transform-row-toggle" type="button" data-role="toggle" aria-expanded="${collapsed ? "false" : "true"}" title="Sbalit / rozbalit">
              <strong>${escapeHtml(queryTransformActionLabel(action))}</strong>
              <span class="query-transform-row-chevron" aria-hidden="true">▾</span>
            </button>
          </div>
          <div class="query-transform-row-body" data-role="body" ${collapsed ? "hidden" : ""}>
            <p class="field-note query-transform-row-description">${escapeHtml(action.description)}</p>
            ${hasInstructionField ? `
              <label class="field">
                <span>Instrukce pro LLM</span>
                <textarea data-role="instruction" rows="2" placeholder="Např. Přelož dotaz do angličtiny.">${escapeHtml(state.instruction || "")}</textarea>
              </label>
            ` : ""}
            <div class="query-transform-row-controls">
              <button class="secondary" type="button" data-role="run">${escapeHtml(queryTransformRunLabel(action))}</button>
              <p class="field-note query-transform-row-status" data-role="status" role="status" aria-live="polite"></p>
            </div>
            <label class="field" data-role="result-field" ${hasResult ? "" : "hidden"}>
              <span>Upravený dotaz</span>
              <textarea data-role="result" rows="2">${escapeHtml(state.result || "")}</textarea>
            </label>
            <label class="field inline-field" title="Ve výchozím nastavení se upravený dotaz používá pouze k vyhledání podkladů v databázi. Model generující odpověď dostane původní dotaz.">
              <input type="checkbox" data-role="use-for-answer" ${state.useForAnswer ? "checked" : ""} />
              <span>Použít i pro generování odpovědi (nejen pro vyhledání v databázi)</span>
            </label>
          </div>
        </div>`;
    })
    .join("");
  updateQueryTransformRowSelectionUi();
}

function updateQueryTransformRowSelectionUi() {
  queryTransformRowsEl?.querySelectorAll("[data-action-row]").forEach((row) => {
    const actionId = row.dataset.actionRow;
    const isSelected = actionId === queryTransformSelectedActionId;
    row.classList.toggle("is-selected", isSelected);
    const selectButton = row.querySelector('[data-role="select"]');
    if (selectButton) {
      const title = isSelected ? "Vybraná transformace" : "Vybrat tuto transformaci";
      selectButton.title = title;
      selectButton.setAttribute("aria-label", title);
    }
  });
}

function findQueryTransformRow(actionId) {
  return [...(queryTransformRowsEl?.querySelectorAll("[data-action-row]") || [])].find(
    (row) => row.dataset.actionRow === actionId,
  ) || null;
}

function setRowCollapsed(actionId, collapsed) {
  const state = queryTransformRowState[actionId];
  if (state) {
    state.collapsed = collapsed;
  }
  const row = findQueryTransformRow(actionId);
  if (!row) {
    return;
  }
  row.classList.toggle("is-collapsed", collapsed);
  const body = row.querySelector('[data-role="body"]');
  if (body) {
    body.hidden = collapsed;
  }
  const toggle = row.querySelector('[data-role="toggle"]');
  if (toggle) {
    toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
  }
}

// Selecting a transform collapses the others down to just their header, so
// the user isn't juggling several open result boxes at once; each stays
// reachable by expanding it again (and re-running it re-selects it).
function collapseOtherRows(selectedActionId) {
  Object.keys(queryTransformRowState).forEach((id) => {
    setRowCollapsed(id, id !== selectedActionId);
  });
}

function syncAppliedQueryTransformFromRow(actionId) {
  const state = queryTransformRowState[actionId];
  if (!state) {
    return;
  }
  const retrievalQuery = String(state.result || "").trim();
  if (!retrievalQuery) {
    if (queryTransformSelectedActionId === actionId) {
      queryTransformSelectedActionId = null;
      appliedQueryTransform = null;
      updateQueryTransformRowSelectionUi();
      renderQueryTransformSection();
    }
    return;
  }
  appliedQueryTransform = {
    originalQuestion: question.value,
    retrievalQuery,
    useForAnswer: Boolean(state.useForAnswer),
    actionId,
  };
  renderQueryTransformSection();
}

// Shared by a live run (executeQueryTransformRow) and restoring a history entry
// (applyHistoryEntryToForm): pushes a resolved result into both the row's state
// and its DOM so the two paths render identically.
function applyQueryTransformRowResult(actionId, resultText, useForAnswer) {
  const state = queryTransformRowState[actionId];
  if (!state) {
    return;
  }
  state.result = resultText;
  if (useForAnswer !== undefined) {
    state.useForAnswer = Boolean(useForAnswer);
  }
  const row = findQueryTransformRow(actionId);
  const resultField = row?.querySelector('[data-role="result"]');
  const resultFieldWrap = row?.querySelector('[data-role="result-field"]');
  const selectButton = row?.querySelector('[data-role="select"]');
  const useForAnswerCheckbox = row?.querySelector('[data-role="use-for-answer"]');
  if (resultField) {
    resultField.value = resultText;
  }
  if (resultFieldWrap) {
    resultFieldWrap.hidden = false;
  }
  if (selectButton) {
    selectButton.disabled = false;
  }
  if (useForAnswer !== undefined && useForAnswerCheckbox) {
    useForAnswerCheckbox.checked = state.useForAnswer;
  }
}

function setQueryTransformSectionBusy(busy) {
  queryTransformRowsEl?.querySelectorAll('[data-role="run"]').forEach((button) => {
    button.disabled = busy;
  });
}

async function executeQueryTransformRow(
  action,
  { signal = null, propagateError = false, manageBusy = true, turnId = null } = {},
) {
  const actionId = String(action.id);
  const state = queryTransformRowState[actionId];
  if (!state) {
    throw new Error("Vybraná transformace není dostupná.");
  }
  const row = findQueryTransformRow(actionId);
  const statusEl = row?.querySelector('[data-role="status"]');
  const actionType = String(action.type || "").toLowerCase();
  const instruction = actionType === "llm" ? String(state.instruction || "").trim() : null;
  if (manageBusy) {
    setQueryTransformSectionBusy(true);
  }
  if (statusEl) {
    statusEl.textContent = actionType === "lindat" ? "Překládám dotaz..." : "Upravuji dotaz pomocí LLM...";
    statusEl.classList.remove("error");
  }
  const effectiveTurnId = turnId || newAnalyticsId();
  try {
    const transformStarted = performance.now();
    const activePrompt = activePromptPresetMetadata();
    const response = await fetch("query-transform", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal,
      analyticsTurnId: effectiveTurnId,
      body: JSON.stringify({
        question: question.value,
        wp_id: activeWpId,
        prompt_preset_id: activePrompt.id,
        action_id: action.id,
        // Local browser personas do not exist on the server, so include their
        // resolved action definition as well as its stable id.
        action,
        instruction,
        model: selectedModelValue(),
        llm_provider: llmProvider.value,
        llm_base_url: nullableString(selectedProviderBaseUrl()),
        llm_api_key: nullableString(selectedProviderApiKey()),
        admin_password: llmModelsUnlocked ? nullableString(llmUnlockPassword.value) : null,
      }),
    });
    const data = await safeJson(response);
    if (!response.ok) {
      throw new Error(data.detail || `Dotaz se nepodařilo upravit (HTTP ${response.status}).`);
    }
    applyQueryTransformRowResult(actionId, String(data.transformed_query || ""));
    state.durationMs = Math.max(0, Math.round(performance.now() - transformStarted));
    state.turnId = effectiveTurnId;
    queryTransformSelectedActionId = actionId;
    queryTransformApplyEnabled = true;
    if (queryTransformApplyToggle) {
      queryTransformApplyToggle.checked = true;
    }
    syncAppliedQueryTransformFromRow(actionId);
    updateQueryTransformRowSelectionUi();
    collapseOtherRows(actionId);
    if (statusEl) {
      statusEl.textContent = "Upravený dotaz je připravený. Můžeš ho ještě ručně změnit.";
    }
  } catch (error) {
    if (statusEl) {
      statusEl.textContent = error.name === "AbortError"
        ? "Úprava dotazu byla zrušena."
        : (error.message || "Dotaz se nepodařilo upravit.");
      statusEl.classList.toggle("error", error.name !== "AbortError");
    }
    if (propagateError) {
      throw error;
    }
  } finally {
    if (manageBusy) {
      setQueryTransformSectionBusy(false);
    }
  }
}

function renderQueryTransformSection() {
  if (!queryTransformSection) {
    return;
  }
  const config = resolvedQueryTransformConfig();
  queryTransformSection.hidden = !config;
  if (!config) {
    refreshAppliedQueryTransformNote(false);
    return;
  }
  const questionChanged = queryTransformRowsQuestion !== question.value;
  const actionIds = config.actions.map((action) => String(action.id));
  const idsChanged = actionIds.length !== Object.keys(queryTransformRowState).length
    || actionIds.some((id) => !queryTransformRowState[id]);
  if (questionChanged || idsChanged) {
    const initialActionId = actionIds.includes(String(config.default_action || ""))
      ? String(config.default_action)
      : actionIds[0];
    queryTransformRowState = {};
    config.actions.forEach((action) => {
      queryTransformRowState[action.id] = {
        result: "",
        useForAnswer: Boolean(action.use_transformed_for_answer),
        instruction: "",
        collapsed: String(action.id) !== initialActionId,
      };
    });
    queryTransformRowsQuestion = question.value;
    queryTransformSelectedActionId = initialActionId;
    queryTransformApplyEnabled = config.auto_apply;
    buildQueryTransformRowsDom(config);
  }
  if (queryTransformApplyToggle) {
    queryTransformApplyToggle.checked = queryTransformApplyEnabled !== false;
  }
  queryTransformSection.classList.toggle("is-disabled", queryTransformApplyEnabled === false);
  const hasAppliedQuery = Boolean(
    appliedQueryTransform
    && appliedQueryTransform.originalQuestion === question.value
    && appliedQueryTransform.retrievalQuery,
  );
  queryTransformSection.classList.toggle("is-applied", hasAppliedQuery);
  refreshAppliedQueryTransformNote(hasAppliedQuery);
}

queryTransformRowsEl?.addEventListener("click", (event) => {
  const selectButton = event.target.closest('[data-role="select"]');
  if (selectButton) {
    const row = selectButton.closest("[data-action-row]");
    const actionId = row?.dataset.actionRow;
    const state = actionId ? queryTransformRowState[actionId] : null;
    if (state) {
      queryTransformSelectedActionId = actionId;
      appliedQueryTransform = null;
      if (String(state.result || "").trim()) {
        syncAppliedQueryTransformFromRow(actionId);
      }
      updateQueryTransformRowSelectionUi();
      collapseOtherRows(actionId);
    }
    return;
  }
  const toggleButton = event.target.closest('[data-role="toggle"]');
  if (toggleButton) {
    const row = toggleButton.closest("[data-action-row]");
    const actionId = row?.dataset.actionRow;
    const state = actionId ? queryTransformRowState[actionId] : null;
    if (state) {
      setRowCollapsed(actionId, !state.collapsed);
    }
    return;
  }
  const runButton = event.target.closest('[data-role="run"]');
  if (!runButton) {
    return;
  }
  const row = runButton.closest("[data-action-row]");
  const actionId = row?.dataset.actionRow;
  const config = resolvedQueryTransformConfig();
  const action = config?.actions.find((item) => String(item.id) === actionId);
  if (action) {
    executeQueryTransformRow(action);
  }
});

queryTransformApplyToggle?.addEventListener("change", () => {
  queryTransformApplyEnabled = queryTransformApplyToggle.checked;
  if (!queryTransformApplyEnabled) {
    appliedQueryTransform = null;
  } else if (queryTransformSelectedActionId) {
    syncAppliedQueryTransformFromRow(queryTransformSelectedActionId);
  }
  renderQueryTransformSection();
});

queryTransformRowsEl?.addEventListener("input", (event) => {
  const row = event.target.closest("[data-action-row]");
  const actionId = row?.dataset.actionRow;
  const state = actionId ? queryTransformRowState[actionId] : null;
  if (!state) {
    return;
  }
  if (event.target.dataset.role === "result") {
    state.result = event.target.value;
    if (queryTransformSelectedActionId === actionId) {
      syncAppliedQueryTransformFromRow(actionId);
    }
  } else if (event.target.dataset.role === "instruction") {
    state.instruction = event.target.value;
  }
});

queryTransformRowsEl?.addEventListener("change", (event) => {
  if (event.target.dataset.role !== "use-for-answer") {
    return;
  }
  const row = event.target.closest("[data-action-row]");
  const actionId = row?.dataset.actionRow;
  const state = actionId ? queryTransformRowState[actionId] : null;
  if (!state) {
    return;
  }
  state.useForAnswer = event.target.checked;
  if (queryTransformSelectedActionId === actionId) {
    syncAppliedQueryTransformFromRow(actionId);
  }
});

function refreshAppliedQueryTransformNote(hasAppliedQuery) {
  if (!appliedQueryTransformNote) {
    return;
  }
  if (!hasAppliedQuery) {
    appliedQueryTransformNote.hidden = true;
    appliedQueryTransformNote.textContent = "";
    return;
  }
  const usage = appliedQueryTransform.useForAnswer
    ? "použije se i pro generování odpovědi"
    : "použije se jen pro vyhledávání zdrojů";
  appliedQueryTransformNote.textContent = `Upravený dotaz: „${appliedQueryTransform.retrievalQuery}“ — ${usage}.`;
  appliedQueryTransformNote.hidden = false;
}

function activeQueryTransformPayload({ includeAnswerFlag = true } = {}) {
  if (
    queryTransformApplyEnabled === false
    || !appliedQueryTransform
    || appliedQueryTransform.originalQuestion !== question.value
    || !String(appliedQueryTransform.retrievalQuery || "").trim()
  ) {
    return {};
  }
  const payload = {
    retrieval_query: appliedQueryTransform.retrievalQuery.trim(),
    query_transform_ms: queryTransformRowState[appliedQueryTransform.actionId]?.durationMs ?? null,
    query_transform_kind: resolvedQueryTransformConfig()?.actions
      ?.find((action) => String(action.id) === String(appliedQueryTransform.actionId))?.type === "llm"
      ? "llm"
      : "other",
  };
  if (includeAnswerFlag) {
    payload.use_retrieval_query_for_answer = Boolean(appliedQueryTransform.useForAnswer);
  }
  return payload;
}

// Not sent to the server (it has no use for it) — only recorded in history so
// that reloading the entry can re-select the exact row that produced it.
function activeQueryTransformActionId() {
  if (
    queryTransformApplyEnabled === false
    || !appliedQueryTransform
    || appliedQueryTransform.originalQuestion !== question.value
    || !String(appliedQueryTransform.retrievalQuery || "").trim()
  ) {
    return null;
  }
  return appliedQueryTransform.actionId || null;
}

function activeQueryTransformTurnId() {
  const actionId = activeQueryTransformActionId();
  return actionId ? queryTransformRowState[actionId]?.turnId || null : null;
}

function pendingAutomaticQueryTransform() {
  const config = resolvedQueryTransformConfig();
  if (!config || queryTransformApplyEnabled === false) {
    return null;
  }
  const action = config.actions.find(
    (item) => String(item.id) === queryTransformSelectedActionId,
  );
  if (!action) {
    return null;
  }
  const state = queryTransformRowState[String(action.id)];
  const hasCurrentResult = Boolean(
    state
    && String(state.result || "").trim()
    && appliedQueryTransform
    && appliedQueryTransform.originalQuestion === question.value
    && appliedQueryTransform.actionId === String(action.id),
  );
  return hasCurrentResult ? null : action;
}

async function prepareAutomaticQueryTransform(signal, turnId) {
  const action = pendingAutomaticQueryTransform();
  if (!action) {
    return;
  }
  statusEl.className = "status";
  statusEl.textContent = "Upravuji dotaz před vyhledáváním...";
  await executeQueryTransformRow(action, {
    signal,
    propagateError: true,
    manageBusy: false,
    turnId,
  });
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
  const options = getWpConfigs()
    .map((wp) => `<option value="${escapeHtml(wp.id)}">${escapeHtml(wp.label || wp.id)}</option>`)
    .join("");
  wpSelect.innerHTML = options;
  wpSelect.value = activeWpId;
  if (settingsWpSelect) {
    settingsWpSelect.innerHTML = options;
    settingsWpSelect.value = settingsWpScope();
  }
}

// Open the Settings dialog scoped to a WP: initialize settingsWpId to the active
// WP, reflect it in the selector, and load that WP's prompts into the editor.
function syncSettingsWp(wpId) {
  settingsWpId = resolveWpId(wpId);
  if (settingsWpSelect) {
    settingsWpSelect.value = settingsWpId;
  }
  // Load the Settings-scoped WP's currently-selected (or default) prompt into the
  // shared editor. Keep the loaded prompt if it already belongs to this WP.
  const keepCurrent = presetWpId(getPromptPresetById(activePromptPresetId)) === settingsWpId;
  applyPromptPresetById(keepCurrent ? activePromptPresetId : defaultPromptPresetId(settingsWpId));
}

// Switch the active work package: pick its default collection and prompt, which
// in turn loads the WP's length definitions and re-renders the WP-filtered
// prompt options. Pass explicit ids when restoring a saved conversation.
function selectWp(wpId, { promptId, collectionId } = {}) {
  const previousWpId = activeWpId;
  const questionSnapshot = question.value;
  const questionRevisionSnapshot = questionEditRevision;
  const matchesCachedPreparedQuestion = questionMatchesPreparedList(
    questionSnapshot,
    predefinedQuestionsByWp.get(previousWpId) || [],
  );
  const managedQuestionSnapshot = managedQuestion?.value === questionSnapshot
    || matchesCachedPreparedQuestion;
  if (matchesCachedPreparedQuestion && managedQuestion?.value !== questionSnapshot) {
    managedQuestion = { wpId: previousWpId, value: questionSnapshot };
  }
  activeWpId = resolveWpId(wpId);
  wpSelect.value = activeWpId;
  const wp = getWpConfig(activeWpId);
  populateMsearchCollections(collectionId || wpDefaultCollectionMsearchId(wp));
  updateRescoreThresholdNote();
  const targetPrompt = promptId && promptPresetExists(promptId)
    ? promptId
    : defaultPromptPresetId(activeWpId);
  applyPromptPresetById(targetPrompt);
  loadPredefinedQuestions(activeWpId, {
    previousWpId,
    questionSnapshot,
    questionRevisionSnapshot,
    managedQuestionSnapshot,
  });
}

const AI_UFAL_HOST = "ai.ufal.mff.cuni.cz";

// Whether a WP's collections are only retrievable via the AI Ufal provider.
// Gating lives on the WP (requires_aiufal), not on individual collection ids,
// which change as new collection versions are published.
function wpRequiresAiufal(wp) {
  return Boolean(wp?.requires_aiufal);
}

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
  const response = await fetch("settings", { analyticsAppOpen: true });
  const settings = await response.json();
  logLlmModelRefresh("page-load", settings);
  appSettings = settings;
  localPlaceholderDefs = loadLocalPlaceholderDefs();
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
  msearchMinConfidence.value = settings.msearch_defaults?.min_confidence ?? 0;
  topK.value = settings.msearch_defaults?.max_results ?? settings.top_k ?? 10;
  systemPrompt.value = settings.prompt_defaults?.system_prompt || "";
  userPromptTemplate.value = settings.prompt_defaults?.user_prompt_template || "";
  updatePromptTemplateWarning();
  topKValue.value = topK.value;
  minRelativeScore.value = settings.retrieval_defaults?.min_relative_score ?? 0.3;
  msearchRescore.checked = Boolean(settings.retrieval_defaults?.msearch_rescore);
  updateMsearchConfidenceLabel();
  updateThresholdLabels();
  updateRescoreThresholdNote();
  applyTheme(localStorage.getItem("theme") || "light");
  renderHistory();
  renderConversationWorkspace();
  await loadPromptPresets();
  renderGlobalPlaceholderDefs();
  loadPredefinedQuestions(activeWpId, {
    initializeQuestion: true,
    questionSnapshot: question.value,
    questionRevisionSnapshot: questionEditRevision,
  });
}

// Shared by the "Odpovědět" form submit (full answer) and the "Pouze vyhledat
// zdroje" button (retrieval only). `retrieveOnlyMode` picks the branch.
// Tracks the in-flight main-panel request so the cancel button can abort it.
// Aborting the fetch also disconnects the SSE stream, which makes the backend
// generator stop retrieval / reranking / generation at its next yield.
let activeQueryController = null;

async function runQuery(retrieveOnlyMode) {
  const controller = new AbortController();
  const turnId = activeQueryTransformTurnId() || newAnalyticsId();
  activeQueryController = controller;
  submitButton.disabled = true;
  retrieveButton.disabled = true;
  setQueryTransformSectionBusy(true);
  cancelButton.hidden = false;
  cancelButton.disabled = false;
  statusEl.className = "status";
  statusEl.textContent = retrieveOnlyMode
    ? "Vyhledávám zdroje..."
    : "Vyhledávám zdroje a generuji odpověď...";
  streamedAnswerText = "";
  currentAnswerSources = [];
  currentRetrievedChunks = [];
  currentRetrievalQuery = question.value;
  currentAnswerQuestion = "";
  currentOmittedChunks = [];
  currentBaselineChunks = [];
  baselineVisible = false;
  currentMsearchRescoreUsed = msearchRescore.checked;
  currentBudgetWarnings = [];
  currentTokenBudget = null;
  currentConversationSummary = "";
  currentReasoning = "";
  renderReasoning("");
  // `Pouze vyhledat zdroje` produces no answer, so there is nothing to reorder by.
  mainSourcesView = Avatar.createSourcesView({ canFlip: !retrieveOnlyMode });
  activeCitation = null;
  renderAnswer("");
  sourcesEl.innerHTML = "";
  baselineSourcesEl.innerHTML = "";
  renderBaselineComparison();
  stopRerankCountdown();
  loadingIndicator.hidden = false;
  const promptNoteSnapshot = activePromptPresetMetadata().note;

  try {
    await prepareAutomaticQueryTransform(controller.signal, turnId);
    statusEl.textContent = retrieveOnlyMode
      ? "Vyhledávám zdroje..."
      : "Vyhledávám zdroje a generuji odpověď...";
    if (retrieveOnlyMode) {
      const payload = buildRetrievePayload();
      currentRetrievalQuery = payload.retrieval_query || payload.question;
      const data = await streamRetrieveWithHandlers(payload, {
        onPreliminarySources(prelimData) {
          currentRetrievalQuery = prelimData.retrieval_query || currentRetrievalQuery;
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
          currentRetrievalQuery = sourceData.retrieval_query || currentRetrievalQuery;
          stopRerankCountdown();
          currentRetrievedChunks = sourceData.retrieved_chunks || [];
          currentBaselineChunks = sourceData.baseline_chunks || [];
          currentAnswerSources = sourceData.sources || chunksToSources(currentRetrievedChunks);
          renderSources(currentAnswerSources, currentRetrievedChunks, "");
          statusEl.textContent = `Nalezeno ${currentRetrievedChunks.length} chunků.`;
        },
      }, { signal: controller.signal, turnId });
      renderAnswer("Zobrazuji pouze nalezené dokumenty. Generování odpovědi bylo vypnuté.");
      statusEl.textContent = `Nalezeno ${data.retrieved_chunks.length} chunků.`;
      currentRetrievedChunks = data.retrieved_chunks || currentRetrievedChunks;
      currentRetrievalQuery = data.retrieval_query || currentRetrievalQuery;
      currentBaselineChunks = data.baseline_chunks || [];
      currentAnswerSources = data.sources || chunksToSources(currentRetrievedChunks);
      completeMainSources(currentAnswerSources, currentRetrievedChunks, "");
      saveHistoryEntry({
        question: question.value,
        mode: "retrieve",
        answer: "Zobrazuji pouze nalezené dokumenty. Generování odpovědi bylo vypnuté.",
        sourceCount: currentRetrievedChunks.length,
        settings: { ...payload, prompt_preset_note: promptNoteSnapshot },
        query_transform_action_id: activeQueryTransformActionId(),
        retrieved_chunks: currentRetrievedChunks,
        sources: currentAnswerSources,
      });
    } else {
      const payload = buildRequestPayload();
      currentRetrievalQuery = payload.retrieval_query || payload.question;
      // Record the verbatim prompt actually used so history/sharing can always
      // show it. The payload sends null when the prompt equals the built-in
      // default (the server fills it in), so read the resolved text directly.
      const promptsUsed = {
        prompt_preset_note: promptNoteSnapshot,
        system_prompt: systemPrompt.value,
        user_prompt_template: userPromptTemplate.value,
      };
      const data = await chatRequest(payload, {
        onPreliminarySources(prelimData) {
          currentRetrievalQuery = prelimData.retrieval_query || currentRetrievalQuery;
          currentAnswerQuestion = prelimData.answer_question || currentAnswerQuestion;
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
          currentRetrievalQuery = sourceData.retrieval_query || currentRetrievalQuery;
          currentAnswerQuestion = sourceData.answer_question || currentAnswerQuestion;
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
        onReasoning(delta) {
          currentReasoning += delta;
          renderReasoning(currentReasoning, { streaming: true });
        },
        onToken(token) {
          if (!streamedAnswerText) {
            collapseReasoning();
          }
          streamedAnswerText += token;
          renderAnswer(streamedAnswerText);
        },
        onDone(doneData) {
          currentRetrievalQuery = doneData.retrieval_query || currentRetrievalQuery;
          currentAnswerQuestion = doneData.answer_question || currentAnswerQuestion;
          const modelLabel = formatModelUsageLabel(doneData.model, doneData.upstream_model);
          statusEl.textContent = formatTimingLabel(doneData, modelLabel);
          currentAnswerSources = doneData.sources || currentAnswerSources;
          currentRetrievedChunks = doneData.retrieved_chunks || currentRetrievedChunks;
          currentBaselineChunks = doneData.baseline_chunks || currentBaselineChunks;
          currentOmittedChunks = doneData.omitted_chunks || currentOmittedChunks;
          currentBudgetWarnings = doneData.chunk_budget_warnings || currentBudgetWarnings;
          currentTokenBudget = doneData.token_budget || currentTokenBudget;
          currentConversationSummary = doneData.conversation_summary || currentConversationSummary;
          currentReasoning = doneData.reasoning || currentReasoning;
          renderReasoning(currentReasoning);
          renderSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
        },
      }, { signal: controller.signal, turnId });
      streamedAnswerText = data.answer || streamedAnswerText;
      renderAnswer(streamedAnswerText);
      currentAnswerSources = data.sources || currentAnswerSources;
      currentRetrievedChunks = data.retrieved_chunks || currentRetrievedChunks;
      currentRetrievalQuery = data.retrieval_query || currentRetrievalQuery;
      currentAnswerQuestion = data.answer_question || currentAnswerQuestion;
      currentBaselineChunks = data.baseline_chunks || currentBaselineChunks;
      currentOmittedChunks = data.omitted_chunks || currentOmittedChunks;
      currentBudgetWarnings = data.chunk_budget_warnings || currentBudgetWarnings;
      currentTokenBudget = data.token_budget || currentTokenBudget;
      currentConversationSummary = data.conversation_summary || currentConversationSummary;
      currentReasoning = data.reasoning || currentReasoning;
      renderReasoning(currentReasoning);
      completeMainSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
      saveHistoryEntry({
        question: question.value,
        mode: "chat",
        answer: data.answer || streamedAnswerText,
        sourceCount: data.retrieved_chunks?.length || 0,
        settings: { ...payload, ...promptsUsed },
        query_transform_action_id: activeQueryTransformActionId(),
        retrieved_chunks: data.retrieved_chunks || [],
        omitted_chunks: data.omitted_chunks || [],
        token_budget: data.token_budget || null,
        chunk_budget_warnings: data.chunk_budget_warnings || [],
        conversation_summary: data.conversation_summary || null,
        reasoning: data.reasoning || "",
        sources: data.sources || [],
        model_used: data.model || model.value,
        upstream_model: data.upstream_model || null,
        response_time_seconds: data.response_time_seconds,
        rerank_time_seconds: data.rerank_time_seconds ?? null,
        generation_time_seconds: data.generation_time_seconds ?? null,
      });
    }
  } catch (error) {
    if (error.name === "AbortError") {
      statusEl.className = "status";
      statusEl.textContent = "Zrušeno.";
    } else {
      statusEl.className = "status error";
      statusEl.textContent = error.message;
    }
  } finally {
    if (activeQueryController === controller) {
      activeQueryController = null;
    }
    stopRerankCountdown();
    loadingIndicator.hidden = true;
    cancelButton.hidden = true;
    submitButton.disabled = false;
    retrieveButton.disabled = false;
    setQueryTransformSectionBusy(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runQuery(false);
});

retrieveButton.addEventListener("click", () => runQuery(true));

function queryTransformActionLabel(action) {
  if (action.label) {
    return String(action.label);
  }
  if (String(action.type).toLowerCase() === "lindat") {
    const source = String(action.source_language || "").toUpperCase();
    const target = String(action.target_language || "").toUpperCase();
    return source && target ? `Přeložit ${source} → ${target}` : "Přeložit";
  }
  return "Upravit pomocí LLM";
}

question.addEventListener("input", () => {
  questionEditRevision += 1;
  managedQuestion = null;
  clearAppliedQueryTransform();
});

cancelButton.addEventListener("click", () => {
  cancelButton.disabled = true;
  statusEl.className = "status";
  statusEl.textContent = "Ruším...";
  activeQueryController?.abort();
});

randomQuestionButton.addEventListener("click", async () => {
  randomQuestionButton.disabled = true;
  statusEl.className = "status";
  statusEl.textContent = "Vybírám náhodnou otázku...";
  const requestedWpId = activeWpId;
  const questionRevisionSnapshot = questionEditRevision;
  try {
    const params = new URLSearchParams({ wp_id: requestedWpId });
    const response = await fetch(`questions/random?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Nepodařilo se vybrat náhodnou otázku.");
    }
    if (activeWpId !== requestedWpId || questionEditRevision !== questionRevisionSnapshot) {
      statusEl.className = "status";
      statusEl.textContent = "";
      return;
    }
    question.value = data.question || "";
    questionEditRevision += 1;
    managedQuestion = { wpId: requestedWpId, value: question.value };
    clearAppliedQueryTransform();
    question.focus();
    statusEl.textContent = "Náhodná otázka je vložená. Spusť odpověď tlačítkem Odpovědět.";
  } catch (error) {
    statusEl.className = "status error";
    statusEl.textContent = error.message;
  } finally {
    randomQuestionButton.disabled = false;
  }
});

function closePredefinedQuestions() {
  if (!predefinedQuestionList) {
    return;
  }
  predefinedQuestionList.hidden = true;
  predefinedQuestionButton?.setAttribute("aria-expanded", "false");
}

function openPredefinedQuestions() {
  if (!predefinedQuestionList || !predefinedQuestionList.children.length) {
    return;
  }
  predefinedQuestionList.hidden = false;
  predefinedQuestionButton?.setAttribute("aria-expanded", "true");
}

async function questionsForWp(wpId) {
  if (predefinedQuestionsByWp.has(wpId)) {
    return { questions: predefinedQuestionsByWp.get(wpId), error: false };
  }
  if (predefinedQuestionLoadsByWp.has(wpId)) {
    return predefinedQuestionLoadsByWp.get(wpId);
  }

  const load = (async () => {
    try {
      const params = new URLSearchParams({ wp_id: wpId || "" });
      const response = await fetch(`questions?${params.toString()}`);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Nepodařilo se načíst otázky.");
      }
      const questions = (data.questions || [])
        .map((item) => String(item).trim())
        .filter(Boolean);
      predefinedQuestionsByWp.set(wpId, questions);
      return { questions, error: false };
    } catch {
      return { questions: [], error: true };
    } finally {
      predefinedQuestionLoadsByWp.delete(wpId);
    }
  })();
  predefinedQuestionLoadsByWp.set(wpId, load);
  return load;
}

function questionMatchesPreparedList(value, questions) {
  const normalized = String(value || "").trim();
  return Boolean(normalized) && questions.some((item) => item === normalized);
}

// Fills the "Připravené otázky" dropdown with the same question list used for
// random questions. It also inserts the first question initially and replaces
// a previous WP's prepared question on WP changes, while preserving custom text.
async function loadPredefinedQuestions(
  wpId = wpSelect.value || "",
  {
    previousWpId = "",
    initializeQuestion = false,
    questionSnapshot = question.value,
    questionRevisionSnapshot = questionEditRevision,
    managedQuestionSnapshot = managedQuestion?.value === question.value,
  } = {},
) {
  if (!predefinedQuestionList) {
    return;
  }
  const renderRevision = ++predefinedQuestionsRenderRevision;
  closePredefinedQuestions();
  const destinationPromise = questionsForWp(wpId);
  const previousPromise = previousWpId && previousWpId !== wpId
    ? questionsForWp(previousWpId)
    : Promise.resolve({ questions: [], error: false });
  const [destination, previous] = await Promise.all([destinationPromise, previousPromise]);

  if (renderRevision !== predefinedQuestionsRenderRevision || activeWpId !== wpId) {
    return;
  }

  if (destination.error || !destination.questions.length) {
    predefinedQuestionList.innerHTML =
      `<li class="predefined-question-empty">Žádné připravené otázky.</li>`;
  } else {
    predefinedQuestionList.innerHTML = destination.questions
      .map((q) => `<li role="option" title="${escapeHtml(q)}">${escapeHtml(q)}</li>`)
      .join("");
  }

  const questionUnchanged = questionEditRevision === questionRevisionSnapshot
    && question.value === questionSnapshot;
  const initialEmptyQuestion = initializeQuestion && !String(questionSnapshot).trim();
  const initialQuestionStillPending = previousWpId
    && previousWpId !== wpId
    && questionRevisionSnapshot === 0
    && !String(questionSnapshot).trim();
  const previousPreparedQuestion = previousWpId
    && previousWpId !== wpId
    && questionMatchesPreparedList(questionSnapshot, previous.questions);
  if (
    questionUnchanged
    && (managedQuestionSnapshot || initialEmptyQuestion || initialQuestionStillPending || previousPreparedQuestion)
  ) {
    question.value = destination.questions[0] || "";
    managedQuestion = { wpId, value: question.value };
    clearAppliedQueryTransform();
  }
}

predefinedQuestionButton?.addEventListener("click", () => {
  if (predefinedQuestionList?.hidden) {
    openPredefinedQuestions();
  } else {
    closePredefinedQuestions();
  }
});

predefinedQuestionList?.addEventListener("click", (event) => {
  const item = event.target.closest("li");
  if (!item || item.classList.contains("predefined-question-empty")) {
    return;
  }
  question.value = item.textContent;
  questionEditRevision += 1;
  managedQuestion = { wpId: activeWpId, value: question.value };
  clearAppliedQueryTransform();
  closePredefinedQuestions();
  question.focus();
});

document.addEventListener("click", (event) => {
  if (predefinedQuestionWrap && !predefinedQuestionWrap.contains(event.target)) {
    closePredefinedQuestions();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closePredefinedQuestions();
    setActiveCitation(null);
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
  // Scope the Settings editors to the active WP on open; the user can switch.
  syncSettingsWp(activeWpId);
  renderGlobalPlaceholderDefs();
  renderInlinePlaceholderDefs();
  renderQueryTransformSettings();
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
settingsDialog.addEventListener("close", () => {
  // If the user edited a different WP in Settings, restore the shared editor to the
  // main page's active WP so the main page (which shares the prompt editor state)
  // is left consistent with its own #wpSelect.
  if (settingsWpId && settingsWpId !== activeWpId) {
    settingsWpId = activeWpId;
    if (presetWpId(getPromptPresetById(activePromptPresetId)) !== activeWpId) {
      applyPromptPresetById(defaultPromptPresetId(activeWpId));
    } else {
      renderPromptPresets(activePromptPresetId);
    }
  }
});

historyButton.addEventListener("click", () => {
  renderAuthorName();
  setHistoryTab("mine");
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
historyTabMine.addEventListener("click", () => setHistoryTab("mine"));
historyTabShared.addEventListener("click", () => setHistoryTab("shared"));
historyAuthorName.addEventListener("click", () => {
  const input = window.prompt("Jméno pro sdílení:", getAuthorName());
  if (input !== null) {
    setAuthorName(input);
    renderAuthorName();
  }
});
shareSelectedButton.addEventListener("click", () => {
  shareSelectedEntries();
});

conversationButton.addEventListener("click", () => {
  openConversationWorkspace();
});
closeConversationButton.addEventListener("click", () => {
  conversationDialog.close();
});
conversationDialog.addEventListener("click", (event) => {
  if (event.target === conversationDialog) {
    conversationDialog.close();
  }
});
// Centralize restore so it also covers closing via the Escape key.
conversationDialog.addEventListener("close", () => {
  restoreMainSettings();
});
newConversationButton.addEventListener("click", () => {
  createConversation();
  if (conversationSettingsActive) {
    applyConversationSettings(ensureSelectedConversation());
  }
  renderConversationWorkspace();
  conversationQuestion.focus();
});
deleteConversationButton.addEventListener("click", () => {
  deleteSelectedConversation();
  if (conversationSettingsActive) {
    applyConversationSettings(ensureSelectedConversation());
  }
});
convWpSelect?.addEventListener("change", () => {
  // Changing WP resets prompt + collection to that WP's defaults. Uses a lighter
  // apply than selectWp so the main page's shared retrieval controls (backend,
  // top_k, weights) are never mutated from conversation mode.
  applyConvWp(convWpSelect.value);
  mirrorConversationControls();
  updateConvModelContextWindowNote();
  persistActiveConversationSettings();
});
convPromptSelect?.addEventListener("change", () => {
  applyPromptPresetById(convPromptSelect.value);
  mirrorConversationControls();
  persistActiveConversationSettings();
});
convProvider?.addEventListener("change", () => {
  llmProvider.value = convProvider.value;
  loadProviderValues(convProvider.value, { preferStored: true });
  refreshModelOptions(appSettings);
  mirrorConversationControls();
  resetConvContextWindowToSelectedModel();
  updateConvModelContextWindowNote();
  persistActiveConversationSettings();
});
convModel?.addEventListener("change", () => {
  model.value = convModel.value;
  updateCustomModelVisibility(customModelAllowed());
  updateConvCustomModelVisibility();
  resetConvContextWindowToSelectedModel();
  updateConvModelContextWindowNote();
  persistActiveConversationSettings();
});
convCustomModel?.addEventListener("input", () => {
  customModel.value = convCustomModel.value;
  updateConvModelContextWindowNote();
  persistActiveConversationSettings();
});
convContextWindowTokens?.addEventListener("input", () => {
  updateConvModelContextWindowNote();
  persistActiveConversationSettings();
});
// Placeholder controls update the global placeholderSelections via their own
// listeners; this delegated listener persists the result after they run.
convPlaceholderControls?.addEventListener("input", persistActiveConversationSettings);
convPlaceholderControls?.addEventListener("change", persistActiveConversationSettings);
conversationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await submitConversationTurn();
});
conversationCancelButton?.addEventListener("click", () => {
  conversationCancelButton.disabled = true;
  activeConversationController?.abort();
});
conversationRewriteQuery?.addEventListener("change", () => {
  const conversation = ensureSelectedConversation();
  updateConversation({
    ...conversation,
    rewrite_query_for_retrieval: conversationRewriteQuery.checked,
    updatedAt: new Date().toISOString(),
  });
  renderConversationWorkspace();
});
exportLegacyHistoryButton?.addEventListener("click", exportLegacyHistory);
deleteLegacyHistoryButton?.addEventListener("click", deleteLegacyHistory);
document.addEventListener("click", pulseSourceCardFromCitation);
document.addEventListener("click", toggleCitationHighlightFromSource);
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
  saveEntryListSafely(
    HISTORY_STORAGE_KEY,
    remainingHistory,
    compactStoredHistoryEntry,
    "history entries",
  );
  selectedHistoryId = remainingHistory[0]?.id ?? null;
  renderHistory();
});

topK.addEventListener("input", () => {
  topKValue.value = topK.value;
});

function updateMsearchConfidenceLabel() {
  msearchMinConfidenceValue.value = Number(msearchMinConfidence.value).toFixed(2);
}

function updateThresholdLabels() {
  minRelativeScoreValue.value = Number(minRelativeScore.value).toFixed(2);
}

msearchMinConfidence.addEventListener("input", updateMsearchConfidenceLabel);
minRelativeScore.addEventListener("input", updateThresholdLabels);

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
settingsWpSelect?.addEventListener("change", () => syncSettingsWp(settingsWpSelect.value));
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
    setPromptPresetStatus(error.message, "error");
  } finally {
    savePromptAsButton.disabled = false;
  }
});
updatePromptButton.addEventListener("click", async () => {
  if (!canUpdatePromptPreset(promptPreset.value)) {
    return;
  }
  updatePromptButton.disabled = true;
  try {
    if (isServerPromptPreset(promptPreset.value)
      || (isDraftPromptPreset(promptPreset.value) && sharePromptOnServer.checked)) {
      await saveCurrentPromptPreset({ mode: "update" });
    } else {
      await saveCurrentPromptPresetLocally({ mode: "update" });
    }
  } catch (error) {
    setPromptPresetStatus(error.message, "error");
  } finally {
    updateUpdatePromptButtonState(promptPreset.value);
  }
});
newPromptButton.addEventListener("click", createBlankPromptDraft);
deletePromptButton.addEventListener("click", async () => {
  deletePromptButton.disabled = true;
  try {
    await deleteSelectedPromptPreset();
  } catch (error) {
    setPromptPresetStatus(error.message, "error");
  } finally {
    updateDeletePromptButtonState(promptPreset.value);
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
  updateContextWindowForSelectedModel();
  populateMsearchCollections(msearchCollection.value);
  updateRescoreThresholdNote();
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
customModel.addEventListener("input", () => {
  persistLlmSettings();
  updateContextWindowForSelectedModel();
});
model.addEventListener("change", () => {
  updateCustomModelVisibility(customModelAllowed());
  persistLlmSettings();
  updateContextWindowForSelectedModel();
  if (model.value === CUSTOM_MODEL_VALUE) {
    customModel.focus();
  }
});
llmUnlockPassword.addEventListener("input", () => {
  llmModelsUnlocked = false;
  setUnlockStatus("");
  persistLlmSettings();
  refreshModelOptions(appSettings);
  updatePromptActionButtonStates(promptPreset.value);
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
[contextWindowTokens, mainContextWindowTokens].forEach((input) => {
  input?.addEventListener("input", () => {
    contextWindowManuallyEdited = true;
    syncContextWindowTokenInputs(input);
    persistTokenBudgetSettings();
    updateModelContextWindowNote();
  });
});
[outputBudgetShort, outputBudgetMedium, outputBudgetLong, minPromptChunks, tokenBudgetSafetyMargin, conversationSummaryTriggerTokens].forEach((input) => {
  input.addEventListener("input", persistTokenBudgetSettings);
});
unlockModelsButton.addEventListener("click", () => verifyUnlockPassword());
logoutAdminButton.addEventListener("click", logoutAdminAccess);
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
    // wp_id / prompt_preset_id / prompt_preset_name are carried for the saved
    // history entry's labels (rendered client-side); the server ignores them and
    // resolves prompts/collections from system_prompt + msearch_collection.
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
    reasoning_effort: nullableString(reasoningEffort?.value),
    admin_password: llmModelsUnlocked ? nullableString(llmUnlockPassword.value) : null,
    top_k: Number(topK.value),
    retrieval_backend: "msearch",
    msearch_collection: msearchCollection.value,
    msearch_mode: "hybrid",
    msearch_min_confidence: nullableNumber(msearchMinConfidence.value),
    msearch_rescore: msearchRescore.checked,
    min_relative_score: nullableNumber(minRelativeScore.value),
    rerank_enabled: false,
    ...activeQueryTransformPayload(),
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
    retrieval_backend: "msearch",
    msearch_collection: msearchCollection.value,
    msearch_mode: "hybrid",
    msearch_min_confidence: nullableNumber(msearchMinConfidence.value),
    msearch_rescore: msearchRescore.checked,
    min_relative_score: nullableNumber(minRelativeScore.value),
    rerank_enabled: false,
    ...activeQueryTransformPayload({ includeAnswerFlag: false }),
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
          ? `Bez admin přístupu jsou pro ${providerLabel} dostupné aktuálně načtené veřejné modely: ${publicModels.join(", ")}.`
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
  // Quota-safe: a full localStorage must NOT throw here. This runs inside the
  // admin-unlock try/catch, where a raw setItem throw would be misreported as a
  // failed login. Returns whether the settings were actually persisted.
  return trySetLocalStorageJson(LLM_SETTINGS_STORAGE_KEY, {
    selected_provider: llmSettingsState.selected_provider,
    provider_settings: llmSettingsState.provider_settings,
    admin_password: llmSettingsState.admin_password,
  });
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
  const provider = getLlmProviders(appSettings).find((item) => item.id === normalizedProviderId);
  return provider?.base_url || "";
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
    updatePromptActionButtonStates(promptPreset.value);
    renderQueryTransformSettings();
    if (!silent) {
      setUnlockStatus("Zadej admin heslo.", "error");
      statusEl.className = "status error";
      statusEl.textContent = "Zadej admin heslo.";
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
      throw new Error("Admin heslo není správné.");
    }
    llmModelsUnlocked = true;
    // Unlock already succeeded server-side; persisting is best-effort, so a full
    // localStorage must not turn a valid login into a failure.
    const persisted = persistLlmSettings();
    refreshModelOptions(appSettings);
    updatePromptActionButtonStates(promptPreset.value);
    renderQueryTransformSettings();
    if (!silent) {
      if (persisted) {
        setUnlockStatus("Admin přístup je aktivní.", "success");
        statusEl.className = "status";
        statusEl.textContent = "Admin přístup je aktivní.";
      } else {
        setUnlockStatus(
          "Admin přístup je aktivní pro tuto relaci, ale nepodařilo se ho uložit (plné úložiště prohlížeče – zkus smazat historii).",
          "success",
        );
        statusEl.className = "status";
        statusEl.textContent = "Admin přístup je aktivní (neuložen – plné úložiště).";
      }
    }
    return true;
  } catch (error) {
    llmModelsUnlocked = false;
    refreshModelOptions(appSettings);
    updatePromptActionButtonStates(promptPreset.value);
    renderQueryTransformSettings();
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

function logoutAdminAccess() {
  llmModelsUnlocked = false;
  llmUnlockPassword.value = "";
  persistLlmSettings();
  refreshModelOptions(appSettings);
  renderPromptPresets();
  renderPlaceholderControls();
  renderQueryTransformSettings();
  updatePromptShareNote();
  setUnlockStatus("Admin přístup byl odhlášen.", "success");
  statusEl.className = "status";
  statusEl.textContent = "Admin přístup byl odhlášen.";
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
  setModelRefreshStatus("Obnovuji modely a kolekce...");
  try {
    const response = await fetch("llm-providers/refresh", { method: "POST" });
    const data = await safeJson(response);
    if (!response.ok) {
      throw new Error(formatErrorDetail(data.detail || "Nepodařilo se obnovit seznam modelů."));
    }
    logLlmModelRefresh("manual-refresh", data);
    applyLlmSettingsUpdate(data, previousProvider);
    refreshModelOptions(appSettings);
    if (Array.isArray(data.wps)) {
      // Live mSearch collections came back too; refresh the selector in place,
      // keeping the current collection selected when it still exists.
      appSettings.wps = data.wps;
      populateMsearchCollections(msearchCollection.value);
    }
    if (previousModel && Array.from(model.options).some((option) => option.value === previousModel)) {
      model.value = previousModel;
      updateContextWindowForSelectedModel();
    }
    renderProviderApiKeyFields();
    const provider = selectedProviderConfig(appSettings);
    const modelCount = Array.isArray(provider?.model_presets) ? provider.model_presets.length : 0;
    const collectionCount = getWpConfig(activeWpId)?.collections?.length ?? 0;
    setModelRefreshStatus(
      `Aktualizováno: ${modelCount} modelů, ${collectionCount} kolekcí v této WP.`,
      "success",
    );
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
    model_context_windows:
      data.model_context_windows && typeof data.model_context_windows === "object"
        ? data.model_context_windows
        : appSettings.model_context_windows,
    provider_context_window_defaults:
      data.provider_context_window_defaults && typeof data.provider_context_window_defaults === "object"
        ? data.provider_context_window_defaults
        : appSettings.provider_context_window_defaults,
    model_reasoning:
      data.model_reasoning && typeof data.model_reasoning === "object"
        ? data.model_reasoning
        : appSettings.model_reasoning,
    provider_reasoning_defaults:
      data.provider_reasoning_defaults && typeof data.provider_reasoning_defaults === "object"
        ? data.provider_reasoning_defaults
        : appSettings.provider_reasoning_defaults,
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
  contextWindowManuallyEdited = stored.context_window_tokens !== undefined && stored.context_window_tokens !== null;
  setContextWindowTokensValue(
    stored.context_window_tokens ?? selectedModelContextWindow() ?? defaultContextWindowTokens(settings),
  );
  outputBudgetShort.value = stored.output_token_budget_short ?? defaults.output_token_budget_short ?? 384;
  outputBudgetMedium.value = stored.output_token_budget_medium ?? defaults.output_token_budget_medium ?? 768;
  outputBudgetLong.value = stored.output_token_budget_long ?? defaults.output_token_budget_long ?? 1024;
  minPromptChunks.value = stored.min_prompt_chunks ?? defaults.min_prompt_chunks ?? 3;
  tokenBudgetSafetyMargin.value = stored.token_budget_safety_margin ?? defaults.token_budget_safety_margin ?? 0.1;
  conversationSummaryTriggerTokens.value =
    stored.conversation_summary_trigger_tokens ?? defaults.conversation_summary_trigger_tokens ?? 3000;
  updateModelContextWindowNote();
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

function defaultContextWindowTokens(settings = appSettings) {
  return settings.token_budget_defaults?.context_window_tokens ?? 32768;
}

function selectedModelContextWindow(modelName = selectedModelValue(), provider = selectedProviderConfig()) {
  const modelKey = String(modelName || "").trim();
  if (!modelKey) {
    return null;
  }
  const providerWindows =
    provider?.model_context_windows && typeof provider.model_context_windows === "object"
      ? provider.model_context_windows
      : {};
  const globalWindows =
    appSettings.model_context_windows && typeof appSettings.model_context_windows === "object"
      ? appSettings.model_context_windows
      : {};
  const tokens = providerWindows[modelKey] ?? globalWindows[modelKey];
  const parsed = Number(tokens);
  if (Number.isFinite(parsed) && parsed >= 1024) {
    return parsed;
  }
  const providerDefault = Number(provider?.default_context_window_tokens);
  return Number.isFinite(providerDefault) && providerDefault >= 1024 ? providerDefault : null;
}

function formatTokenCount(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toLocaleString("cs-CZ") : "";
}

function setContextWindowTokensValue(value) {
  const nextValue = value ?? "";
  if (contextWindowTokens) {
    contextWindowTokens.value = nextValue;
  }
  if (mainContextWindowTokens) {
    mainContextWindowTokens.value = nextValue;
  }
}

function syncContextWindowTokenInputs(sourceInput) {
  const value = sourceInput?.value ?? "";
  if (sourceInput !== contextWindowTokens && contextWindowTokens) {
    contextWindowTokens.value = value;
  }
  if (sourceInput !== mainContextWindowTokens && mainContextWindowTokens) {
    mainContextWindowTokens.value = value;
  }
}

function updateContextWindowForSelectedModel({ force = false, persist = false } = {}) {
  if (!force && contextWindowManuallyEdited) {
    updateModelContextWindowNote();
    refreshReasoningEffortOptions();
    return;
  }
  setContextWindowTokensValue(selectedModelContextWindow() ?? defaultContextWindowTokens());
  if (persist) {
    persistTokenBudgetSettings();
  }
  updateModelContextWindowNote();
  refreshReasoningEffortOptions();
}

// Reasoning support is server-declared data — `data/models.json` plus whatever
// the provider's own catalogue publishes — not something the client knows how
// to guess. A model that declares nothing gets no control at all and no
// reasoning parameter is sent, which is the old behaviour.
const REASONING_DEFAULT_VALUE = "";

function selectedModelReasoning(modelName = selectedModelValue(), provider = selectedProviderConfig()) {
  const byModel = appSettings.model_reasoning && typeof appSettings.model_reasoning === "object"
    ? appSettings.model_reasoning
    : {};
  const byProvider =
    appSettings.provider_reasoning_defaults && typeof appSettings.provider_reasoning_defaults === "object"
      ? appSettings.provider_reasoning_defaults
      : {};
  const modelKey = String(modelName || "").trim();
  const support = byModel[modelKey] || byProvider[String(provider?.label || "").trim()] || null;
  return support && Array.isArray(support.efforts) && support.efforts.length ? support : null;
}

const REASONING_EFFORT_LABELS = {
  none: "vypnuto",
  minimal: "minimální",
  low: "nízké",
  medium: "střední",
  high: "vysoké",
  xhigh: "velmi vysoké",
  max: "maximální",
};

function refreshReasoningEffortOptions() {
  if (!reasoningEffortField || !reasoningEffort) {
    return;
  }
  const support = selectedModelReasoning();
  if (!support) {
    reasoningEffortField.hidden = true;
    reasoningEffort.innerHTML = "";
    return;
  }
  const previous = reasoningEffort.value;
  const defaultLabel = support.default
    ? `Výchozí (${REASONING_EFFORT_LABELS[support.default] || support.default})`
    : "Výchozí";
  const options = [`<option value="${REASONING_DEFAULT_VALUE}">${escapeHtml(defaultLabel)}</option>`].concat(
    support.efforts.map(
      (effort) => `<option value="${escapeHtml(effort)}">${escapeHtml(REASONING_EFFORT_LABELS[effort] || effort)}</option>`,
    ),
  );
  reasoningEffort.innerHTML = options.join("");
  reasoningEffort.value = support.efforts.includes(previous) ? previous : REASONING_DEFAULT_VALUE;
  reasoningEffortField.hidden = false;
}

// Some models reason whether or not they are asked to. Showing the trace beats
// discarding it silently, but it is not part of the answer, so it stays folded.
//
// While it streams it is the exception: a reasoning model writes its whole
// trace before its first answer token, so for those seconds the trace is the
// only thing happening and the panel is worth having open. `collapseReasoning`
// folds it again as soon as the answer starts.
function renderReasoning(text, { streaming = false } = {}) {
  if (!reasoningPanel || !reasoningText) {
    return;
  }
  const trimmed = String(text || "").trim();
  reasoningPanel.hidden = !trimmed;
  reasoningText.textContent = trimmed;
  if (streaming && trimmed) {
    reasoningPanel.open = true;
    reasoningText.scrollTop = reasoningText.scrollHeight;
  }
}

function collapseReasoning() {
  if (reasoningPanel) {
    reasoningPanel.open = false;
  }
}

function updateModelContextWindowNote() {
  if (!modelContextWindowNote) {
    return;
  }
  const knownWindow = selectedModelContextWindow();
  const currentWindow = nullableInteger(contextWindowTokens?.value);
  modelContextWindowNote.classList.remove("warning");
  if (knownWindow) {
    if (currentWindow && currentWindow > knownWindow) {
      modelContextWindowNote.classList.add("warning");
      modelContextWindowNote.textContent =
        `Známé maximum pro tento model: ${formatTokenCount(knownWindow)} tokenů. `
        + `Aktuálně používáte ${formatTokenCount(currentWindow)} tokenů, takže se kontext nemusí vejít.`;
      return;
    }
    const suffix =
      currentWindow && currentWindow !== knownWindow
        ? ` Aktuálně používáte ${formatTokenCount(currentWindow)} tokenů.`
        : "";
    modelContextWindowNote.textContent = `Známé maximum pro tento model: ${formatTokenCount(knownWindow)} tokenů.${suffix}`;
    return;
  }
  modelContextWindowNote.textContent =
    `Pro tento model nemáme uložené maximum. Výchozí hodnota aplikace: ${formatTokenCount(defaultContextWindowTokens())} tokenů.`;
}

async function chatRequest(payload, handlers = {}, { signal, turnId = null } = {}) {
  if (providerSupportsStreaming(payload.llm_provider)) {
    return streamChatWithHandlers(payload, handlers, { signal, turnId });
  }
  const data = await fetchChat(payload, { signal, turnId });
  handlers.onSources?.(data);
  if (data.answer) {
    handlers.onToken?.(data.answer, data);
  }
  handlers.onDone?.(data);
  return data;
}

async function fetchChat(payload, { signal, turnId = null } = {}) {
  const response = await fetch("chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
    analyticsTurnId: turnId,
  });
  const data = await safeJson(response);
  if (!response.ok) {
    throw new Error(formatErrorDetail(data.detail || "Request failed"));
  }
  return data;
}

async function streamRetrieveWithHandlers(payload, handlers = {}, { signal, turnId = null } = {}) {
  const response = await fetch("retrieve/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
    analyticsTurnId: turnId,
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
      if (event.event === "status") {
        handlers.onStatus?.(event.data);
      } else if (event.event === "preliminary_sources") {
        handlers.onPreliminarySources?.(event.data);
      } else if (event.event === "rerank_progress") {
        handlers.onRerankProgress?.(event.data);
      } else if (event.event === "sources") {
        handlers.onSources?.(event.data);
      } else if (event.event === "done") {
        donePayload = event.data;
        handlers.onDone?.(donePayload);
      } else if (event.event === "error") {
        throw requestError(event.data.detail, "Streaming retrieve failed");
      }
      separatorIndex = buffer.indexOf("\n\n");
    }
    if (done) {
      break;
    }
  }

  if (!donePayload) {
    throw new Error("Streaming finished without retrieval results.");
  }
  return donePayload;
}

function providerSupportsStreaming(providerId = null) {
  const provider = getLlmProviders(appSettings).find(
    (item) => item.id === normalizeProviderId(providerId || llmProvider.value || appSettings.llm_provider || ""),
  );
  return provider?.supports_streaming !== false;
}

async function streamChatWithHandlers(payload, handlers = {}, { signal, turnId = null } = {}) {
  const response = await fetch("chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
    analyticsTurnId: turnId,
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
      if (event.event === "status") {
        handlers.onStatus?.(event.data);
      } else if (event.event === "preliminary_sources") {
        handlers.onPreliminarySources?.(event.data);
      } else if (event.event === "rerank_progress") {
        handlers.onRerankProgress?.(event.data);
      } else if (event.event === "sources") {
        handlers.onSources?.(event.data);
      } else if (event.event === "reasoning") {
        handlers.onReasoning?.(event.data.text || "", event.data);
      } else if (event.event === "token") {
        handlers.onToken?.(event.data.text || "", event.data);
      } else if (event.event === "done") {
        donePayload = event.data;
        handlers.onDone?.(donePayload);
      } else if (event.event === "error") {
        throw requestError(event.data.detail, "Streaming failed");
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
  updateContextWindowForSelectedModel();
}

// System placeholders are filled by the server and never surfaced as a control.
const SYSTEM_PLACEHOLDERS = new Set(["question", "retrieved_snippets", "current_date"]);

// System placeholders are filled by the server and cannot be edited or deleted.
// Surfaced read-only in the "Proměnné promptu" list for discoverability.
const SYSTEM_PLACEHOLDER_INFO = [
  { name: "question", label: "Otázka uživatele", note: "doplní server z dotazu" },
  { name: "retrieved_snippets", label: "Nalezený kontext", note: "doplní server z nalezených pasáží" },
  { name: "current_date", label: "Aktuální datum", note: "doplní server (datum na serveru)" },
];

// Minimal user template for a new blank prompt: keeps the {question} and
// {retrieved_snippets} system tokens so the draft works without manual setup.
const BLANK_USER_PROMPT_TEMPLATE = "Otázka:\n{question}\n\nNalezený kontext:\n{retrieved_snippets}";

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
  renderQueryTransformSettings();
}

// Describe where an effective global def currently comes from, for the list.
function globalPlaceholderDefSource(name) {
  if (Object.prototype.hasOwnProperty.call(localGlobalPlaceholderDefs(), name)) {
    return "local";
  }
  const record = globalSharedPlaceholderRecord(name);
  if (record && (record.owner_id || record.updated_at)) {
    return "shared";
  }
  return "builtin";
}

function globalSharedPlaceholderRecord(name) {
  return (Array.isArray(appSettings.placeholders) ? appSettings.placeholders : [])
    .find((item) => item && item.name === name && (item.owner_id || item.updated_at)) || null;
}

function canShareGlobalPlaceholder(name) {
  const slug = slugifyPlaceholderName(name);
  if (!slug) {
    return true;
  }
  const record = globalSharedPlaceholderRecord(slug);
  if (CODE_FLOOR_PLACEHOLDERS.has(slug)) {
    return llmModelsUnlocked;
  }
  if (!record) {
    return true;
  }
  return record.owner_id === getBrowserOwnerId() || llmModelsUnlocked;
}

function canDeleteGlobalPlaceholder(name, source) {
  if (source === "local") {
    return true;
  }
  if (source !== "shared") {
    return false;
  }
  const record = globalSharedPlaceholderRecord(name);
  return Boolean(record) && (record.owner_id === getBrowserOwnerId() || llmModelsUnlocked);
}

const PLACEHOLDER_SOURCE_LABELS = {
  local: "lokální (jen tento prohlížeč)",
  shared: "sdílená (server)",
  builtin: "vestavěná",
};

function placeholderDefDetailsHtml(def) {
  const help = def.help ? `<p><strong>Nápověda:</strong> ${escapeHtml(def.help)}</p>` : "";
  const defaultValue = def.default ? escapeHtml(def.default) : "nenastaveno";
  const options = Array.isArray(def.options) && def.options.length
    ? `<ul>${def.options.map((option) => `
        <li><code>${escapeHtml(option.name)}</code> ${escapeHtml(option.label || option.name)}<br><span>${escapeHtml(option.text || "")}</span></li>
      `).join("")}</ul>`
    : "";
  return `
    <div class="placeholder-def-details" hidden>
      ${help}
      <p><strong>Výchozí hodnota:</strong> ${defaultValue}</p>
      ${options}
    </div>`;
}

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
  const systemRows = SYSTEM_PLACEHOLDER_INFO
    .map((info) => `
        <div class="placeholder-def-row placeholder-def-row--system" data-system-placeholder="${escapeHtml(info.name)}">
          <div class="placeholder-def-meta">
            <strong>${escapeHtml(info.label)}</strong>
            <code>{${escapeHtml(info.name)}}</code>
            <span class="field-note">systémová · ${escapeHtml(info.note)}</span>
          </div>
        </div>`)
    .join("");
  globalPlaceholderDefsList.innerHTML = systemRows + sorted
    .map((name) => {
      const source = globalPlaceholderDefSource(name);
      const def = localGlobalPlaceholderDefs()[name] || globalPlaceholderDefs()[name] || {};
      const sourceLabel = PLACEHOLDER_SOURCE_LABELS[source] || source;
      const kindLabel = def.kind === "select" ? "výběr" : "text";
      const canDelete = canDeleteGlobalPlaceholder(name, source);
      return `
        <div class="placeholder-def-row" data-global-placeholder="${escapeHtml(name)}">
          <div class="placeholder-def-meta">
            <strong>${escapeHtml(def.label || name)}</strong>
            <code>{${escapeHtml(name)}}</code>
            <span class="field-note">${escapeHtml(kindLabel)} · ${escapeHtml(sourceLabel)}</span>
          </div>
          <div class="inline-actions">
            <button class="secondary" type="button" data-view-global="${escapeHtml(name)}">Zobrazit</button>
            <button class="secondary" type="button" data-edit-global="${escapeHtml(name)}">Upravit</button>
            ${!canDelete
              ? ""
              : `<button class="secondary danger-lite" type="button" data-delete-global="${escapeHtml(name)}" data-delete-scope="${source}">Smazat</button>`}
          </div>
          ${placeholderDefDetailsHtml(def)}
        </div>`;
    })
    .join("");
}

function renderInlinePlaceholderDefs() {
  if (!inlinePlaceholderDefsList) {
    return;
  }
  const preset = getPromptPresetById(activePromptPresetId);
  const editable = canEditPromptSpecificPlaceholders(activePromptPresetId);
  if (newInlinePlaceholderButton) {
    newInlinePlaceholderButton.disabled = !editable;
  }
  if (!preset) {
    inlinePlaceholderDefsList.innerHTML = `<p class="field-note">Nejdřív vyber prompt.</p>`;
    return;
  }
  const inline = activePromptInlinePlaceholderDefs();
  const names = Object.keys(inline).sort();
  const disabledNote = !editable
    ? `<p class="field-note unsaved-note">${SAVE_PROMPT_BEFORE_VARIABLES_MESSAGE}</p>`
    : "";
  if (!names.length) {
    inlinePlaceholderDefsList.innerHTML = `<p class="field-note">Tento prompt nemá žádné vlastní proměnné.</p>${disabledNote}`;
    return;
  }
  inlinePlaceholderDefsList.innerHTML = `${names
    .map((name) => {
      const def = inline[name] || {};
      const kindLabel = def.kind === "select" ? "výběr" : "text";
      return `
        <div class="placeholder-def-row" data-inline-placeholder="${escapeHtml(name)}">
          <div class="placeholder-def-meta">
            <strong>${escapeHtml(def.label || name)}</strong>
            <code>{${escapeHtml(name)}}</code>
            <span class="field-note">${escapeHtml(kindLabel)}</span>
          </div>
          <div class="inline-actions">
            ${editable
              ? `<button class="secondary" type="button" data-edit-inline="${escapeHtml(name)}">Upravit</button>
                 <button class="secondary danger-lite" type="button" data-delete-inline="${escapeHtml(name)}">Smazat</button>`
              : ""}
          </div>
        </div>`;
    })
    .join("")}${disabledNote}`;
}

// --- query-transform settings (per prompt preset) --------------------------
// The config lives on preset.query_transform itself (same shape the backend
// resolves via resolvedQueryTransformConfig()); editing it mutates the preset
// object in place and persists it the same way inline placeholder defs do:
// immediately, via a local save or a shared "update selected" round-trip.

function activePromptQueryTransform() {
  const preset = getPromptPresetById(activePromptPresetId);
  const qt = preset && preset.query_transform;
  return qt && typeof qt === "object" ? qt : null;
}

function renderQueryTransformSettings() {
  if (!queryTransformEnabledToggle) {
    return;
  }
  const preset = getPromptPresetById(activePromptPresetId);
  const editable = canEditPromptQueryTransform(activePromptPresetId);
  queryTransformEnabledToggle.disabled = !preset || !editable;
  if (queryTransformDisabledNote) {
    queryTransformDisabledNote.hidden = !preset || editable;
    queryTransformDisabledNote.textContent = editable ? "" : queryTransformEditMessage(activePromptPresetId);
  }
  if (newQueryTransformActionButton) {
    newQueryTransformActionButton.disabled = !editable;
  }
  const qt = activePromptQueryTransform();
  if (resetBuiltinQueryTransformButton) {
    resetBuiltinQueryTransformButton.hidden = !(
      isUnshadowedBuiltInPromptPreset(activePromptPresetId)
      && llmModelsUnlocked
      && qt
    );
  }
  const enabled = Boolean(qt?.enabled);
  queryTransformEnabledToggle.checked = enabled;
  if (queryTransformAutoApplyToggle) {
    queryTransformAutoApplyToggle.checked = qt?.auto_apply !== false;
    queryTransformAutoApplyToggle.disabled = !preset || !editable || !enabled;
  }
  if (queryTransformSettingsBody) {
    queryTransformSettingsBody.hidden = !enabled;
  }
  if (!queryTransformActionDefsList) {
    return;
  }
  const actions = Array.isArray(qt?.actions) ? qt.actions : [];
  const disabledNote = !editable
    ? `<p class="field-note unsaved-note">${escapeHtml(queryTransformEditMessage(activePromptPresetId))}</p>`
    : "";
  if (!actions.length) {
    queryTransformActionDefsList.innerHTML = `<p class="field-note">Zatím žádné akce úpravy dotazu.</p>${disabledNote}`;
    return;
  }
  const defaultActionId = qt?.default_action;
  queryTransformActionDefsList.innerHTML = `${actions
    .map((action) => {
      const isDefault = action.id === defaultActionId;
      const typeLabel = action.type === "llm" ? "LLM" : "překlad";
      const answerBadge = action.use_transformed_for_answer ? " · i pro odpověď" : "";
      return `
        <div class="placeholder-def-row" data-query-transform-action="${escapeHtml(action.id)}">
          <div class="placeholder-def-meta">
            <strong>${escapeHtml(action.label || action.id)}</strong>
            <span class="field-note">${escapeHtml(typeLabel)}${isDefault ? " · výchozí" : ""}${answerBadge}</span>
            <label class="field inline-field query-transform-default-action">
              <input
                type="radio"
                name="queryTransformDefaultAction"
                value="${escapeHtml(action.id)}"
                data-default-query-transform-action
                ${isDefault ? "checked" : ""}
                ${editable ? "" : "disabled"}
              />
              <span>Výchozí automatická transformace</span>
            </label>
          </div>
          <div class="inline-actions">
            ${editable
              ? `<button class="secondary" type="button" data-edit-query-transform-action="${escapeHtml(action.id)}">Upravit</button>`
              : ""}
          </div>
        </div>`;
    })
    .join("")}${disabledNote}`;
}

async function updateActiveQueryTransform(mutator) {
  const preset = getPromptPresetById(activePromptPresetId);
  if (!preset) {
    throw new Error("Nejdřív vyber prompt.");
  }
  if (!canEditPromptQueryTransform(activePromptPresetId)) {
    throw new Error(queryTransformEditMessage(activePromptPresetId));
  }
  const builtinOverride = isUnshadowedBuiltInPromptPreset(activePromptPresetId);
  const previous = preset.query_transform ? JSON.parse(JSON.stringify(preset.query_transform)) : null;
  if (!preset.query_transform || typeof preset.query_transform !== "object") {
    preset.query_transform = { enabled: false, auto_apply: true, actions: [] };
  }
  mutator(preset.query_transform);
  if (!Array.isArray(preset.query_transform.actions)) {
    preset.query_transform.actions = [];
  }
  if (!preset.query_transform.actions.some((action) => action.id === preset.query_transform.default_action)) {
    preset.query_transform.default_action = preset.query_transform.actions[0]?.id || null;
  }
  try {
    if (builtinOverride) {
      const response = await fetch(
        `prompt-presets/builtin-overrides/${encodeURIComponent(activePromptPresetId)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query_transform: preset.query_transform,
            admin_password: llmUnlockPassword.value.trim() || null,
          }),
        },
      );
      const data = await safeJson(response);
      if (!response.ok) {
        throw new Error(data.detail || "Transformaci vestavěného profilu se nepodařilo uložit.");
      }
      setBuiltInPromptQueryTransform(activePromptPresetId, data.query_transform);
      setPromptPresetStatus("Transformace vestavěného profilu byla uložena na serveru.", "success");
    } else if (isLocalPromptPreset(activePromptPresetId)) {
      persistLocalPromptPresets();
      setPromptPresetStatus("Transformace dotazu byla uložena lokálně.", "success");
    } else if (isServerPromptPreset(activePromptPresetId)) {
      await saveCurrentPromptPreset({ mode: "update" });
      setPromptPresetStatus("Transformace dotazu byla uložena do sdíleného promptu.", "success");
    }
  } catch (error) {
    preset.query_transform = previous;
    throw error;
  } finally {
    renderQueryTransformSettings();
    // The edited config may have changed action ids/defaults, so force the
    // inline rows to rebuild instead of keeping stale per-action state.
    clearAppliedQueryTransform({ refreshButton: false });
    renderQueryTransformSection();
  }
}

let queryTransformActionEditorId = null;

function updateQueryTransformActionTypeVisibility() {
  const isLlm = queryTransformActionType.value === "llm";
  queryTransformActionLindatFields.hidden = isLlm;
  queryTransformActionLlmFields.hidden = !isLlm;
}

function setQueryTransformActionError(message) {
  if (!queryTransformActionError) {
    return;
  }
  queryTransformActionError.hidden = !message;
  queryTransformActionError.textContent = message || "";
}

function slugifyQueryTransformActionId(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function openQueryTransformActionEditor(actionId) {
  const qt = activePromptQueryTransform();
  const action = actionId ? (qt?.actions || []).find((item) => item.id === actionId) : null;
  queryTransformActionEditorId = actionId || null;
  queryTransformActionType.value = action?.type === "llm" ? "llm" : "lindat";
  queryTransformActionId.value = action?.id || "";
  queryTransformActionLabelInput.value = action?.label || "";
  queryTransformActionDescription.value = action?.description || "";
  queryTransformActionSourceLang.value = action?.source_language || "";
  queryTransformActionTargetLang.value = action?.target_language || "";
  queryTransformActionModel.value = action?.model || "";
  queryTransformActionPrompt.value = action?.prompt_template || "";
  queryTransformActionUseForAnswer.checked = Boolean(action?.use_transformed_for_answer);
  updateQueryTransformActionTypeVisibility();
  setQueryTransformActionError("");
  deleteQueryTransformActionButton.hidden = !actionId;
  queryTransformActionTitle.textContent = actionId ? "Upravit akci úpravy dotazu" : "Nová akce úpravy dotazu";
  queryTransformActionDialog.showModal();
  queryTransformActionId.focus();
}

newQueryTransformActionButton?.addEventListener("click", () => {
  if (!canEditPromptQueryTransform(activePromptPresetId)) {
    setPromptPresetStatus(queryTransformEditMessage(activePromptPresetId), "error");
    return;
  }
  openQueryTransformActionEditor(null);
});

queryTransformActionDefsList?.addEventListener("click", (event) => {
  const editId = event.target?.dataset?.editQueryTransformAction;
  if (editId) {
    openQueryTransformActionEditor(editId);
  }
});

queryTransformActionDefsList?.addEventListener("change", async (event) => {
  if (!event.target.matches("[data-default-query-transform-action]")) {
    return;
  }
  try {
    await updateActiveQueryTransform((qt) => {
      qt.default_action = event.target.value;
    });
  } catch (error) {
    setPromptPresetStatus(error.message, "error");
  }
});

queryTransformActionType?.addEventListener("change", updateQueryTransformActionTypeVisibility);

closeQueryTransformActionButton?.addEventListener("click", () => queryTransformActionDialog.close());
queryTransformActionDialog?.addEventListener("click", (event) => {
  if (event.target === queryTransformActionDialog) {
    queryTransformActionDialog.close();
  }
});

saveQueryTransformActionButton?.addEventListener("click", async () => {
  const type = queryTransformActionType.value === "llm" ? "llm" : "lindat";
  const id = slugifyQueryTransformActionId(queryTransformActionId.value);
  if (!id) {
    setQueryTransformActionError("Zadej platné id (písmena, číslice, pomlčky).");
    return;
  }
  const qtForDuplicateCheck = activePromptQueryTransform();
  const duplicatesOtherAction = (qtForDuplicateCheck?.actions || []).some(
    (item) => item.id === id && item.id !== queryTransformActionEditorId,
  );
  if (duplicatesOtherAction) {
    setQueryTransformActionError("Toto id už jiná akce používá. Zvol jiné.");
    return;
  }
  const description = queryTransformActionDescription.value.trim();
  if (!description) {
    setQueryTransformActionError("Napiš popis transformace pro uživatele.");
    return;
  }
  const action = {
    id,
    label: queryTransformActionLabelInput.value.trim() || id,
    description,
    type,
    use_transformed_for_answer: queryTransformActionUseForAnswer.checked,
  };
  if (type === "lindat") {
    const lindatModel = queryTransformActionModel.value.trim();
    if (!isValidLindatModel(lindatModel)) {
      setQueryTransformActionError("Zadej platný LINDAT model, např. cs-en.");
      return;
    }
    action.model = lindatModel;
    action.source_language = queryTransformActionSourceLang.value.trim();
    action.target_language = queryTransformActionTargetLang.value.trim();
  } else {
    const promptTemplate = queryTransformActionPrompt.value.trim();
    if (!promptTemplate.includes("{question}")) {
      setQueryTransformActionError("Šablona promptu musí obsahovat {question}.");
      return;
    }
    action.prompt_template = promptTemplate;
  }
  try {
    await updateActiveQueryTransform((qt) => {
      const actions = Array.isArray(qt.actions) ? [...qt.actions] : [];
      const previousId = queryTransformActionEditorId;
      const existingIndex = actions.findIndex((item) => item.id === (previousId || id));
      if (existingIndex >= 0) {
        actions[existingIndex] = action;
      } else {
        actions.push(action);
      }
      qt.actions = actions;
      qt.enabled = true;
      if (previousId && qt.default_action === previousId) {
        qt.default_action = id;
      }
    });
    queryTransformActionDialog.close();
  } catch (error) {
    setQueryTransformActionError(error.message);
  }
});

deleteQueryTransformActionButton?.addEventListener("click", async () => {
  if (!queryTransformActionEditorId) {
    queryTransformActionDialog.close();
    return;
  }
  try {
    await updateActiveQueryTransform((qt) => {
      qt.actions = (qt.actions || []).filter((item) => item.id !== queryTransformActionEditorId);
    });
    queryTransformActionDialog.close();
  } catch (error) {
    setQueryTransformActionError(error.message);
  }
});

queryTransformEnabledToggle?.addEventListener("change", async () => {
  const enabled = queryTransformEnabledToggle.checked;
  try {
    await updateActiveQueryTransform((qt) => {
      qt.enabled = enabled;
    });
  } catch (error) {
    setPromptPresetStatus(error.message, "error");
    renderQueryTransformSettings();
  }
});

queryTransformAutoApplyToggle?.addEventListener("change", async () => {
  const autoApply = queryTransformAutoApplyToggle.checked;
  try {
    await updateActiveQueryTransform((qt) => {
      qt.auto_apply = autoApply;
    });
  } catch (error) {
    setPromptPresetStatus(error.message, "error");
    renderQueryTransformSettings();
  }
});

resetBuiltinQueryTransformButton?.addEventListener("click", async () => {
  if (!isUnshadowedBuiltInPromptPreset(activePromptPresetId) || !llmModelsUnlocked) {
    return;
  }
  if (!window.confirm("Odstranit uloženou transformaci a obnovit výchozí nastavení tohoto profilu?")) {
    return;
  }
  resetBuiltinQueryTransformButton.disabled = true;
  try {
    const params = new URLSearchParams({
      admin_password: llmUnlockPassword.value.trim(),
    });
    const response = await fetch(
      `prompt-presets/builtin-overrides/${encodeURIComponent(activePromptPresetId)}?${params.toString()}`,
      { method: "DELETE" },
    );
    if (!response.ok) {
      const data = await safeJson(response);
      throw new Error(data.detail || "Výchozí nastavení transformace se nepodařilo obnovit.");
    }
    deleteBuiltInPromptQueryTransform(activePromptPresetId);
    setPromptPresetStatus("Výchozí nastavení transformace bylo obnoveno.", "success");
    clearAppliedQueryTransform({ refreshButton: false });
    renderQueryTransformSettings();
    renderQueryTransformSection();
  } catch (error) {
    setPromptPresetStatus(error.message, "error");
  } finally {
    resetBuiltinQueryTransformButton.disabled = false;
  }
});

function isValidLindatModel(modelValue) {
  return /^[a-z]{2,3}-[a-z]{2,3}$/i.test(modelValue || "");
}

// --- shared dialog editor ---------------------------------------------------
// editorContext describes where the result is saved:
//   { scope: "global" | "inline", originalName }
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
  if (placeholderDefShareOnServer) {
    placeholderDefShareOnServer.checked = context.scope === "global"
      && context.originalName
      && globalPlaceholderDefSource(context.originalName) === "shared"
      && canShareGlobalPlaceholder(context.originalName);
  }
  updatePlaceholderShareVisibility();
  renderPlaceholderDefActions(context.scope);
  placeholderDefDialog.showModal();
  placeholderDefName.focus();
}

function placeholderScopeNote(scope) {
  if (scope === "global") {
    return "Globální proměnná. Může být lokální jen pro tento prohlížeč, nebo sdílená na serveru.";
  }
  return "Promptová proměnná patří jen k vybranému promptu. Pokud má stejný název jako globální proměnná, použije se tato promptová verze.";
}

function updatePlaceholderShareVisibility() {
  if (!placeholderDefShareField || !placeholderDefShareOnServer || !placeholderDefShareNote) {
    return;
  }
  const context = placeholderEditorContext || {};
  const isGlobal = context.scope === "global";
  placeholderDefShareField.hidden = !isGlobal;
  placeholderDefShareNote.hidden = !isGlobal;
  if (!isGlobal) {
    placeholderDefShareOnServer.checked = false;
    return;
  }
  const slug = slugifyPlaceholderName(placeholderDefName.value || context.originalName);
  const shareAllowed = canShareGlobalPlaceholder(slug);
  placeholderDefShareField.hidden = !shareAllowed;
  placeholderDefShareNote.hidden = false;
  if (!shareAllowed) {
    placeholderDefShareOnServer.checked = false;
    placeholderDefShareNote.textContent = CODE_FLOOR_PLACEHOLDERS.has(slug)
      ? "Serverovou výchozí hodnotu vestavěné proměnné může změnit jen uživatel se sdíleným heslem. Bez něj se změna uloží lokálně."
      : "Tuto sdílenou proměnnou může na serveru změnit jen její vlastník nebo uživatel se sdíleným heslem. Bez oprávnění se změna uloží lokálně.";
    return;
  }
  placeholderDefShareNote.textContent = placeholderDefShareOnServer.checked
    ? "Uloží se na serveru pro všechny uživatele."
    : "Uloží se jen v tomto prohlížeči.";
}

function renderPlaceholderDefActions(scope) {
  const saveLabel = scope === "inline" ? "Uložit proměnnou promptu" : "Uložit";
  placeholderDefActions.innerHTML =
    `<button class="primary" type="button" data-def-action="save">${escapeHtml(saveLabel)}</button>`;
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

function setGlobalPlaceholderDefsStatus(message, variant = "") {
  if (!globalPlaceholderDefsStatus) {
    return;
  }
  globalPlaceholderDefsStatus.textContent = message || "";
  globalPlaceholderDefsStatus.classList.toggle("success", variant === "success");
  globalPlaceholderDefsStatus.classList.toggle("error", variant === "error");
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

async function submitPlaceholderDefEditor() {
  const result = readPlaceholderDefFromEditor();
  if (!result) {
    return;
  }
  const context = placeholderEditorContext || {};
  const targetName = result.name;
  try {
    setPlaceholderDefError("");
    if (context.scope === "global") {
      if (placeholderDefShareOnServer.checked && canShareGlobalPlaceholder(targetName)) {
        await saveSharedGlobalPlaceholderDef(targetName, result.def);
        setGlobalPlaceholderDefsStatus(`Proměnná "{${targetName}}" byla uložena na serveru.`, "success");
      } else {
        saveLocalGlobalPlaceholderDef(targetName, result.def);
        setGlobalPlaceholderDefsStatus(`Proměnná "{${targetName}}" byla uložena lokálně.`, "success");
      }
    } else {
      await saveInlinePlaceholderDef(targetName, result.def);
    }
  } catch (error) {
    setPlaceholderDefError(error.message);
    return;
  }
  placeholderDefDialog.close();
  await refreshAfterPlaceholderDefChange();
}

function saveLocalGlobalPlaceholderDef(name, def) {
  const normalized = normalizePlaceholderDef(name, def);
  if (!normalized) {
    throw new Error("Proměnnou se nepodařilo uložit.");
  }
  localPlaceholderDefs = { ...localPlaceholderDefs, [normalized.name]: normalized.def };
  persistLocalPlaceholderDefs();
}

async function saveSharedGlobalPlaceholderDef(name, def) {
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

// Prompt-scoped defs live on the selected prompt preset. Local and shared prompts
// are persisted immediately; built-ins and unsaved drafts must first be saved as a
// new prompt.
async function saveInlinePlaceholderDef(name, def) {
  let preset = getPromptPresetById(activePromptPresetId);
  if (!preset) {
    throw new Error("Nejdřív vyber prompt.");
  }
  if (!canEditPromptSpecificPlaceholders(activePromptPresetId)) {
    throw new Error(SAVE_PROMPT_BEFORE_VARIABLES_MESSAGE);
  }
  if (!preset.placeholders || typeof preset.placeholders !== "object" || Array.isArray(preset.placeholders)) {
    preset.placeholders = {};
  }
  const previousPlaceholders = { ...preset.placeholders };
  const normalized = normalizePlaceholderDef(name, def);
  if (!normalized) {
    throw new Error("Proměnnou se nepodařilo uložit.");
  }
  preset.placeholders[normalized.name] = normalized.def;
  if (isLocalPromptPreset(activePromptPresetId)) {
    persistLocalPromptPresets();
    setPromptPresetStatus("Proměnná promptu byla uložena lokálně.", "success");
  } else if (isServerPromptPreset(activePromptPresetId)) {
    try {
      await saveCurrentPromptPreset({ mode: "update" });
    } catch (error) {
      preset.placeholders = previousPlaceholders;
      throw error;
    }
    setPromptPresetStatus("Proměnná promptu byla uložena do sdíleného promptu.", "success");
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

async function deleteInlinePlaceholderDef(name) {
  const preset = getPromptPresetById(activePromptPresetId);
  if (!preset || !preset.placeholders) {
    return;
  }
  if (!canEditPromptSpecificPlaceholders(activePromptPresetId)) {
    throw new Error(SAVE_PROMPT_BEFORE_VARIABLES_MESSAGE);
  }
  const previousPlaceholders = { ...preset.placeholders };
  delete preset.placeholders[name];
  if (isLocalPromptPreset(activePromptPresetId)) {
    persistLocalPromptPresets();
    setPromptPresetStatus("Proměnná promptu byla smazána lokálně.", "success");
  } else if (isServerPromptPreset(activePromptPresetId)) {
    try {
      await saveCurrentPromptPreset({ mode: "update" });
    } catch (error) {
      preset.placeholders = previousPlaceholders;
      throw error;
    }
    setPromptPresetStatus("Proměnná promptu byla smazána ze sdíleného promptu.", "success");
  }
}

// --- editor event wiring ----------------------------------------------------
newGlobalPlaceholderButton?.addEventListener("click", () => {
  openPlaceholderDefEditor({ scope: "global", originalName: "" }, null);
});
newInlinePlaceholderButton?.addEventListener("click", () => {
  if (!canEditPromptSpecificPlaceholders(activePromptPresetId)) {
    setPromptPresetStatus(SAVE_PROMPT_BEFORE_VARIABLES_MESSAGE, "error");
    return;
  }
  openPlaceholderDefEditor({ scope: "inline", originalName: "" }, null);
});

globalPlaceholderDefsList?.addEventListener("click", async (event) => {
  const viewButton = event.target.closest("[data-view-global]");
  if (viewButton) {
    const row = viewButton.closest(".placeholder-def-row");
    const details = row?.querySelector(".placeholder-def-details");
    if (details) {
      const isHidden = details.hidden;
      details.hidden = !isHidden;
      viewButton.textContent = isHidden ? "Skrýt" : "Zobrazit";
    }
    return;
  }
  const editButton = event.target.closest("[data-edit-global]");
  if (editButton) {
    const name = editButton.dataset.editGlobal;
    const def = localGlobalPlaceholderDefs()[name] || globalPlaceholderDefs()[name] || null;
    openPlaceholderDefEditor({ scope: "global", originalName: name }, def);
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
        setGlobalPlaceholderDefsStatus(`Proměnná "{${name}}" byla smazána z tohoto prohlížeče.`, "success");
      } else {
        await deleteSharedGlobalPlaceholderDef(name);
        setGlobalPlaceholderDefsStatus(`Proměnná "{${name}}" byla smazána ze serveru.`, "success");
      }
      await refreshAfterPlaceholderDefChange();
    } catch (error) {
      setGlobalPlaceholderDefsStatus(error.message, "error");
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
    if (!window.confirm(`Smazat proměnnou promptu "${name}"?`)) {
      return;
    }
    try {
      await deleteInlinePlaceholderDef(name);
      await refreshAfterPlaceholderDefChange();
    } catch (error) {
      setPromptPresetStatus(error.message, "error");
    }
  }
});

placeholderDefKind?.addEventListener("change", updatePlaceholderKindVisibility);
placeholderDefName?.addEventListener("input", updatePlaceholderShareVisibility);
placeholderDefShareOnServer?.addEventListener("change", updatePlaceholderShareVisibility);
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
    submitPlaceholderDefEditor();
  }
});
closePlaceholderDefButton?.addEventListener("click", () => placeholderDefDialog.close());
placeholderDefForm?.addEventListener("submit", (event) => event.preventDefault());

// Re-render the main-page controls for the active prompt and reset every value to
// its resolved def default. Called on every prompt switch and on prompt-text edits.
function renderPlaceholderControls() {
  activePlaceholderDefs = resolveActivePlaceholderDefs();
  placeholderSelections = {};
  if (!activePlaceholderContainer) {
    return;
  }
  const entries = Object.entries(activePlaceholderDefs);
  activePlaceholderContainer.innerHTML = entries
    .map(([name, def]) => renderPlaceholderControl(name, def))
    .join("");
  for (const [name, def] of entries) {
    placeholderSelections[name] = placeholderDefaultValue(def);
    const control = activePlaceholderContainer.querySelector(`[data-placeholder="${cssAttrEscape(name)}"]`);
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
    const control = activePlaceholderContainer?.querySelector(`[data-placeholder="${cssAttrEscape(name)}"]`);
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
  // The main-page select lists the active WP's prompts; the Settings select lists
  // the Settings-scoped WP's prompts (defaults to activeWpId until the user
  // switches the Settings WP). Both reflect the same loaded prompt (resolvedId).
  renderPromptPresetSelect(activePromptPreset, resolvedId, activeWpId);
  renderPromptPresetSelect(promptPreset, resolvedId, settingsWpScope());
  activePromptPresetId = resolvedId;
  updatePromptActionButtonStates(resolvedId);
  if (newInlinePlaceholderButton) {
    newInlinePlaceholderButton.disabled = !canEditPromptSpecificPlaceholders(resolvedId);
  }
}

function renderPromptPresetSelect(selectEl, selectedId, wpId = activeWpId) {
  const builtinIds = new Set(builtInPromptPresets(wpId).map((preset) => preset.id));
  const serverIds = new Set(promptPresets.map((preset) => preset.id));
  const wpLocal = localPromptPresets.filter((preset) => (
    presetWpId(preset) === wpId
    && !builtinIds.has(preset.id)
    && !serverIds.has(preset.id)
  ));
  const wpServer = promptPresets.filter((preset) => presetWpId(preset) === wpId && !builtinIds.has(preset.id));
  const wpDraft = draftPromptPreset?.is_new && presetWpId(draftPromptPreset) === wpId ? [draftPromptPreset] : [];
  const builtinOptions = builtInPromptPresets(wpId)
    .map((preset) => {
      const effective = getPromptPresetById(preset.id) || preset;
      return `<option value="${escapeHtml(preset.id)}"${promptNoteTitleAttribute(effective)}>${escapeHtml(effective.name || preset.name)}</option>`;
    })
    .join("");
  const draftOptions = wpDraft.length
    ? `<optgroup label="Rozepsané prompty">${wpDraft
        .map((preset) => `<option value="${escapeHtml(preset.id)}"${promptNoteTitleAttribute(preset)}>${escapeHtml(preset.name)}</option>`)
        .join("")}</optgroup>`
    : "";
  const localOptions = wpLocal.length
    ? `<optgroup label="Lokální prompty">${wpLocal
        .map((preset) => `<option value="${escapeHtml(preset.id)}"${promptNoteTitleAttribute(preset)}>Local - ${escapeHtml(preset.name)}</option>`)
        .join("")}</optgroup>`
    : "";
  const serverOptions = wpServer.length
    ? `<optgroup label="Sdílené prompty">${wpServer
        .map((preset) => {
          const ownedSuffix = isOwnedServerPromptPreset(preset.id) ? " (tvůj)" : "";
          return `<option value="${escapeHtml(preset.id)}"${promptNoteTitleAttribute(preset)}>Shared - ${escapeHtml(preset.name)}${ownedSuffix}</option>`;
        })
        .join("")}</optgroup>`
    : "";
  selectEl.innerHTML = `<optgroup label="Vestavěné prompty">${builtinOptions}</optgroup>${draftOptions}${localOptions}${serverOptions}`;
  selectEl.value = normalizePromptPresetId(selectedId);
  selectEl.title = promptPresetNote(getPromptPresetById(selectEl.value));
}

function promptPresetNote(preset) {
  return String(preset?.note || "").trim();
}

function promptNoteTitleAttribute(preset) {
  const note = promptPresetNote(preset);
  return note ? ` title="${escapeHtml(note)}"` : "";
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

function isUnshadowedBuiltInPromptPreset(presetId) {
  return isBuiltInPromptPreset(presetId)
    && !isLocalPromptPreset(presetId)
    && !isServerPromptPreset(presetId);
}

function isLocalPromptPreset(presetId) {
  return localPromptPresets.some((preset) => preset.id === presetId);
}

function isServerPromptPreset(presetId) {
  return promptPresets.some((preset) => preset.id === presetId);
}

function isEditablePromptPreset(presetId) {
  return Boolean(getPromptPresetById(presetId));
}

function isDraftPromptPreset(presetId) {
  return Boolean(draftPromptPreset && draftPromptPreset.id === presetId);
}

function canDeletePromptPreset(presetId) {
  return isLocalPromptPreset(presetId)
    || isDraftPromptPreset(presetId)
    || (isServerPromptPreset(presetId) && (isOwnedServerPromptPreset(presetId) || llmModelsUnlocked));
}

function updateDeletePromptButtonState(presetId) {
  const blockedForeignSharedPrompt = isServerPromptPreset(presetId)
    && !isOwnedServerPromptPreset(presetId)
    && !llmModelsUnlocked;
  deletePromptButton.disabled = !canDeletePromptPreset(presetId);
  deletePromptButton.title = blockedForeignSharedPrompt
    ? "Cizí sdílený prompt nelze smazat."
    : "";
}

function canUpdatePromptPreset(presetId) {
  return isLocalPromptPreset(presetId)
    || isDraftPromptPreset(presetId)
    || (isServerPromptPreset(presetId) && (isOwnedServerPromptPreset(presetId) || llmModelsUnlocked));
}

function updateUpdatePromptButtonState(presetId) {
  const blockedForeignSharedPrompt = isServerPromptPreset(presetId)
    && !isOwnedServerPromptPreset(presetId)
    && !llmModelsUnlocked;
  updatePromptButton.disabled = !canUpdatePromptPreset(presetId);
  if (blockedForeignSharedPrompt) {
    updatePromptButton.title = "Cizí sdílený prompt nelze aktualizovat. Ulož ho jako nový.";
  } else if (isBuiltInPromptPreset(presetId) && !isLocalPromptPreset(presetId) && !isServerPromptPreset(presetId)) {
    updatePromptButton.title = "Vestavěný prompt nejprve ulož jako nový.";
  } else {
    updatePromptButton.title = "";
  }
}

function updatePromptActionButtonStates(presetId) {
  updateDeletePromptButtonState(presetId);
  updateUpdatePromptButtonState(presetId);
}

function canEditPromptSpecificPlaceholders(presetId) {
  return isLocalPromptPreset(presetId) || isServerPromptPreset(presetId);
}

function canEditPromptQueryTransform(presetId) {
  return canEditPromptSpecificPlaceholders(presetId)
    || (isUnshadowedBuiltInPromptPreset(presetId) && llmModelsUnlocked);
}

function queryTransformEditMessage(presetId) {
  return isUnshadowedBuiltInPromptPreset(presetId)
    ? UNLOCK_BUILTIN_QUERY_TRANSFORM_MESSAGE
    : SAVE_PROMPT_BEFORE_QUERY_TRANSFORM_MESSAGE;
}

function setBuiltInPromptQueryTransform(presetId, queryTransform) {
  for (const wp of getWpConfigs()) {
    const preset = (wp.builtin_prompts || []).find((item) => item.id === presetId);
    if (preset) {
      preset.query_transform = queryTransform;
      return;
    }
  }
}

function deleteBuiltInPromptQueryTransform(presetId) {
  for (const wp of getWpConfigs()) {
    const preset = (wp.builtin_prompts || []).find((item) => item.id === presetId);
    if (preset) {
      delete preset.query_transform;
      return;
    }
  }
}

// Built-in prompts are shipped per WP by the backend (appSettings.wps). Each may
// carry an inline `placeholders` map that overrides the global defs wholesale.
function wpBuiltInPromptPresets(wp) {
  if (!wp) {
    return [];
  }
  return (wp.builtin_prompts || []).map((preset) => {
    const normalized = {
      id: preset.id,
      name: preset.name,
      wp_id: wp.id,
      note: String(preset.note || ""),
      system_prompt: preset.system_prompt || "",
      user_prompt_template: preset.user_prompt_template || "",
      placeholders: preset.placeholders && typeof preset.placeholders === "object" ? preset.placeholders : {},
    };
    if (Object.prototype.hasOwnProperty.call(preset, "query_transform")) {
      normalized.query_transform = preset.query_transform;
    }
    return normalized;
  });
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
  return (draftPromptPreset && draftPromptPreset.id === presetId ? draftPromptPreset : null)
    || localPromptPresets.find((preset) => preset.id === presetId)
    || promptPresets.find((preset) => preset.id === presetId)
    || allBuiltInPromptPresets().find((preset) => preset.id === presetId)
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
  promptName.value = preset.name || "";
  promptNote.value = preset.note || "";
  systemPrompt.value = preset.system_prompt || "";
  userPromptTemplate.value = preset.user_prompt_template || "";
  clearAppliedQueryTransform({ refreshButton: false });
  // Switching prompts resets controls to the new prompt's resolved defaults; no
  // prior values (including text placeholders) are preserved across the switch.
  renderPlaceholderControls();
  updatePromptTemplateWarning();
  renderInlinePlaceholderDefs();
  renderQueryTransformSettings();
  renderPromptPresets(resolvedId);
  renderQueryTransformSection();
}

function activePromptPresetMetadata() {
  const preset = getPromptPresetById(activePromptPresetId);
  return {
    id: preset?.id || activePromptPresetId || defaultPromptPresetId(),
    name: preset?.name || activePromptPresetId || "Výchozí",
    note: promptPresetNote(preset),
  };
}

function currentPromptDraft({ id = null, name }) {
  const draft = {
    id,
    name: name.trim(),
    wp_id: activePromptWpId(),
    note: promptNote.value,
    system_prompt: systemPrompt.value,
    user_prompt_template: userPromptTemplate.value,
    // Inline placeholder defs come from the live preset object, which the inline
    // def editor (14d) mutates in place; saving the prompt persists them.
    placeholders: activePromptInlinePlaceholderDefs(),
  };
  const sourcePreset = getPromptPresetById(promptPreset.value);
  if (sourcePreset && Object.prototype.hasOwnProperty.call(sourcePreset, "query_transform")) {
    draft.query_transform = sourcePreset.query_transform;
  }
  return draft;
}

function selectedPromptNameForSave() {
  const preset = getPromptPresetById(promptPreset.value);
  return promptName.value.trim() || preset?.name || "";
}

function promptNameForCreate(promptLabel) {
  if (isDraftPromptPreset(promptPreset.value)) {
    return selectedPromptNameForSave();
  }
  return window.prompt(promptLabel, selectedPromptNameForSave());
}

function settingsWpScope() {
  // The Settings dialog edits the Settings-scoped WP; before it has been opened
  // (settingsWpId empty) it mirrors the active WP.
  return resolveWpId(settingsWpId || activeWpId);
}

function activePromptWpId() {
  // Drafts are saved under the WP currently selected in the Settings dialog.
  return settingsWpScope();
}

async function saveCurrentPromptPreset({ mode }) {
  const isUpdate = mode === "update";
  const currentPreset = isUpdate ? getPromptPresetById(promptPreset.value) : null;
  if (isUpdate && !currentPreset) {
    throw new Error("Vyber uložený prompt, který chceš aktualizovat.");
  }
  // Updates take the editable name field; "Save as new" asks for a name, except
  // for a blank draft that already received its name when it was created.
  const name = isUpdate ? promptName.value : promptNameForCreate("Název promptu");
  if (!name || !name.trim()) {
    return;
  }
  const updateId = isUpdate && !(isDraftPromptPreset(promptPreset.value) && draftPromptPreset?.is_new)
    ? currentPreset.id
    : null;
  const payload = {
    ...currentPromptDraft({ id: updateId, name }),
    owner_id: getBrowserOwnerId(),
    admin_password: llmUnlockPassword.value.trim() || null,
  };
  const response = await fetch("prompt-presets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await safeJson(response);
  if (!response.ok) {
    throw new Error(data.detail || `Sdílený prompt se nepodařilo uložit (HTTP ${response.status}).`);
  }
  removeLocalPromptPreset(data.id);
  draftPromptPreset = null;
  setPromptPresetStatus("Uloženo sdíleně na serveru.", "success");
  await loadPromptPresets(data.id);
}

async function saveCurrentPromptPresetLocally({ mode }) {
  const isUpdate = mode === "update";
  const currentPreset = isUpdate ? getPromptPresetById(promptPreset.value) : null;
  if (isUpdate && !currentPreset) {
    throw new Error("Vyber prompt, který chceš aktualizovat.");
  }
  // Updates take the editable name field; "Save as new" asks for a name, except
  // for a blank draft that already received its name when it was created.
  const name = isUpdate ? promptName.value : promptNameForCreate("Název lokálního promptu");
  if (!name || !name.trim()) {
    return;
  }
  const id = isUpdate && !(isDraftPromptPreset(promptPreset.value) && draftPromptPreset?.is_new)
    ? currentPreset.id
    : createLocalPromptPresetId();
  const nextPreset = currentPromptDraft({ id, name });
  const hasExistingLocal = localPromptPresets.some((preset) => preset.id === id);
  localPromptPresets = hasExistingLocal
    ? localPromptPresets.map((preset) => (preset.id === id ? nextPreset : preset))
    : [...localPromptPresets, nextPreset];
  persistLocalPromptPresets();
  draftPromptPreset = null;
  setPromptPresetStatus("Uloženo lokálně v tomto prohlížeči.", "success");
  applyPromptPresetById(id);
}

function updatePromptShareNote() {
  promptShareNote.textContent = sharePromptOnServer.checked
    ? "Uloží se na serveru a bude dostupný ostatním."
    : "Uloží se jen v tomto prohlížeči.";
}

function setPromptPresetStatus(message, variant = "") {
  if (!promptPresetStatus) {
    return;
  }
  promptPresetStatus.textContent = message || "";
  promptPresetStatus.classList.toggle("success", variant === "success");
  promptPresetStatus.classList.toggle("error", variant === "error");
}

function removeLocalPromptPreset(presetId) {
  if (!presetId || !localPromptPresets.some((preset) => preset.id === presetId)) {
    return;
  }
  localPromptPresets = localPromptPresets.filter((preset) => preset.id !== presetId);
  persistLocalPromptPresets();
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
  if (!id || id.startsWith("draft-") || !name) {
    return null;
  }
  const normalized = {
    id,
    name,
    wp_id: String(item.wp_id || appSettings.default_wp || ""),
    note: String(item.note || ""),
    system_prompt: String(item.system_prompt || ""),
    user_prompt_template: String(item.user_prompt_template || ""),
    // Inline placeholder defs are passed through as-is; the inline def editor
    // (14d) mutates them and persists via persistLocalPromptPresets().
    placeholders: item.placeholders && typeof item.placeholders === "object" && !Array.isArray(item.placeholders)
      ? item.placeholders
      : {},
  };
  if (Object.prototype.hasOwnProperty.call(item, "query_transform")) {
    normalized.query_transform = item.query_transform;
  }
  return normalized;
}

function persistLocalPromptPresets() {
  localStorage.setItem(LOCAL_PROMPT_PRESETS_STORAGE_KEY, JSON.stringify(localPromptPresets));
}

function createBlankPromptDraft() {
  const name = window.prompt("Název promptu", "");
  if (!name || !name.trim()) {
    return;
  }
  // Blank drafts are a Settings-editor action, scoped to the Settings WP.
  const draftId = `draft-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  // A truly empty user template would drop {question}/{retrieved_snippets}, leaving the
  // model with no question and no retrieved passages. Seed the two system tokens
  // the server fills so the draft is functional out of the box.
  draftPromptPreset = {
    id: draftId,
    name: name.trim(),
    wp_id: settingsWpScope(),
    note: "",
    system_prompt: "",
    user_prompt_template: BLANK_USER_PROMPT_TEMPLATE,
    placeholders: {},
    is_new: true,
  };
  activePromptPresetId = draftId;
  promptName.value = draftPromptPreset.name;
  promptNote.value = draftPromptPreset.note;
  systemPrompt.value = draftPromptPreset.system_prompt;
  userPromptTemplate.value = draftPromptPreset.user_prompt_template;
  renderPlaceholderControls();
  updatePromptTemplateWarning();
  renderInlinePlaceholderDefs();
  renderQueryTransformSettings();
  clearAppliedQueryTransform({ refreshButton: false });
  renderQueryTransformSection();
  renderPromptPresets(draftId);
  setPromptPresetStatus("Nový prompt je připravený. Uloží se až po kliknutí na uložení.", "success");
  systemPrompt.focus();
}

function resetPromptEditors() {
  resetPromptEditorValues();
  renderPromptPresets(defaultPromptPresetId(settingsWpScope()));
}

function resetPromptEditorValues() {
  activePromptPresetId = defaultPromptPresetId(settingsWpScope());
  const defaultPrompt = getPromptPresetById(defaultPromptPresetId(settingsWpScope()));
  if (defaultPrompt) {
    promptName.value = defaultPrompt.name || "";
    promptNote.value = defaultPrompt.note || "";
    systemPrompt.value = defaultPrompt.system_prompt || "";
    userPromptTemplate.value = defaultPrompt.user_prompt_template || "";
    renderPlaceholderControls();
    updatePromptTemplateWarning();
  } else {
    promptName.value = "";
    promptNote.value = "";
  }
}

async function deleteSelectedPromptPreset() {
  if (isDraftPromptPreset(promptPreset.value)) {
    draftPromptPreset = null;
    resetPromptEditors();
    setPromptPresetStatus("Rozepsaný prompt byl zahozen.", "success");
    return;
  }
  if (isLocalPromptPreset(promptPreset.value)) {
    localPromptPresets = localPromptPresets.filter((preset) => preset.id !== promptPreset.value);
    persistLocalPromptPresets();
    resetPromptEditors();
    setPromptPresetStatus("Lokální prompt byl smazán.", "success");
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
  setPromptPresetStatus("Sdílený prompt byl smazán.", "success");
  await loadPromptPresets(defaultPromptPresetId(settingsWpScope()));
}

// Collection options are scoped to the active WP. Each WP currently has a
// single collection, but the data model already supports several per WP.
function populateMsearchCollections(currentCollection) {
  const wp = getWpConfig(activeWpId);
  const collections = wp?.collections || [];
  const aiUfalSelected = isAiUfalBaseUrl(currentProviderBaseUrl());
  const wpGated = wpRequiresAiufal(wp) && !aiUfalSelected;
  msearchCollection.innerHTML = collections
    .map((collection) => {
      const value = collection.msearch_collection_id || "";
      const label = collection.label || value;
      const disabled = wpGated ? " disabled" : "";
      return `<option value="${escapeHtml(value)}"${disabled}>${escapeHtml(label)}</option>`;
    })
    .join("");
  const options = Array.from(msearchCollection.options);
  const enabledCurrent = options.find((option) => option.value === currentCollection && !option.disabled);
  const firstEnabled = options.find((option) => !option.disabled);
  msearchCollection.value = enabledCurrent?.value || firstEnabled?.value || options[0]?.value || "";
}

function updateRescoreThresholdNote() {
  // mSearch rescoring rescales scores onto a lower range, so the relative-score
  // threshold can over-filter. Warn only when rescoring is actually in effect.
  rescoreThresholdNote.hidden = !msearchRescore.checked;
}

msearchRescore.addEventListener("change", updateRescoreThresholdNote);

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
    llmPolicyNote.textContent = `Admin přístup je aktivní: pro ${providerLabel} jsou dostupné všechny načtené modely a vlastní model.`;
    return;
  }
  const publicModels = providerPublicModels(provider, appSettings);
  if (publicModels.length > 0) {
    llmPolicyNote.textContent = `Bez admin přístupu jsou pro ${providerLabel} dostupné aktuálně načtené veřejné modely: ${publicModels.join(", ")}.`;
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
  return Avatar.formatRequestErrorDetail(detail);
}

function requestError(detail, fallback) {
  const error = new Error(formatErrorDetail(detail || fallback));
  error.detail = detail;
  return error;
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

function isStorageQuotaError(error) {
  const message = String(error?.message || "").toLowerCase();
  return (
    error?.name === "QuotaExceededError" ||
    error?.name === "NS_ERROR_DOM_QUOTA_REACHED" ||
    error?.code === 22 ||
    error?.code === 1014 ||
    message.includes("quota")
  );
}

function trySetLocalStorageJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    if (!isStorageQuotaError(error)) {
      throw error;
    }
    return false;
  }
}

let conversationStorageFailure = "";
const storageSaveSucceeded = new Map();

function refreshConversationStorageStatus() {
  if (!conversationStorageStatus || !conversationStorageStatusText) {
    return;
  }
  let legacyHistory = "";
  try {
    legacyHistory = localStorage.getItem(LEGACY_HISTORY_STORAGE_KEY) || "";
  } catch {
    // Storage access itself may be disabled. The write failure below remains visible.
  }
  const messages = [];
  if (conversationStorageFailure) {
    messages.push(conversationStorageFailure);
  }
  if (legacyHistory) {
    const sizeMiB = Avatar.approximateLocalStorageMiB(legacyHistory).toFixed(1);
    messages.push(
      `Stará, už nezobrazovaná historie zabírá přibližně ${sizeMiB} MiB. `
      + "Před smazáním ji můžete exportovat.",
    );
  }
  conversationStorageStatus.hidden = messages.length === 0;
  conversationStorageStatusText.textContent = messages.join(" ");
  if (legacyHistoryStorageActions) {
    legacyHistoryStorageActions.hidden = !legacyHistory;
  }
}

function reportStorageSaveFailure(key, label) {
  const message = `Změny se nepodařilo uložit: úložiště prohlížeče je plné. Žádná starší položka nebyla smazána.`;
  console.warn(`[rag-avatar] Could not save ${label}; browser localStorage quota is full. Existing entries were preserved.`);
  if (key === CONVERSATION_STORAGE_KEY) {
    conversationStorageFailure = message;
    refreshConversationStorageStatus();
  } else if (statusEl) {
    statusEl.className = "status error";
    statusEl.textContent = message;
  }
}

function clearStorageSaveFailure(key) {
  if (key !== CONVERSATION_STORAGE_KEY || !conversationStorageFailure) {
    return;
  }
  conversationStorageFailure = "";
  refreshConversationStorageStatus();
}

function compactStoredChunk(chunk) {
  if (!chunk || typeof chunk !== "object") {
    return chunk;
  }
  return {
    ...chunk,
    text: shortenText(chunk.text || "", COMPACT_STORED_CHUNK_TEXT_LIMIT),
  };
}

// Persisted history keeps only what a source card needs — the name + link (from
// metadata) and the score — never the passage text, which is by far the largest
// field. The live in-memory view (currentRetrievedChunks) still has full text;
// this only strips the localStorage copy. Detail/loaded-from-history source
// cards therefore show title + link + score, but no excerpt/highlighting.
function stripStoredChunkText(chunk) {
  if (!chunk || typeof chunk !== "object") {
    return chunk;
  }
  const metadata = { ...(chunk.metadata || {}) };
  delete metadata.original_text;
  return { ...chunk, text: "", metadata };
}

function compactStoredHistoryEntry(entry) {
  return {
    ...entry,
    retrieved_chunks: (entry.retrieved_chunks || []).map(compactStoredChunk),
    omitted_chunks: [],
  };
}

function compactStoredConversation(entry) {
  return Avatar.compactConversationForStorage(entry, {
    chunkTextLimit: COMPACT_STORED_CHUNK_TEXT_LIMIT,
  });
}

function saveEntryListSafely(key, entries, compactEntry, label) {
  const result = Avatar.saveJsonEntryList(localStorage, key, entries, compactEntry);
  if (result.saved) {
    storageSaveSucceeded.set(key, true);
    clearStorageSaveFailure(key);
    return result.entries;
  }

  storageSaveSucceeded.set(key, false);
  reportStorageSaveFailure(key, label);
  return result.entries;
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

function renderQueryUsedInfo() {
  const typedQuestion = question.value.trim();
  if (retrievalQueryInfo && retrievalQueryText) {
    const retrievalQuery = currentRetrievalQuery.trim();
    const changed = retrievalQuery && retrievalQuery !== typedQuestion;
    retrievalQueryInfo.hidden = !changed;
    retrievalQueryText.textContent = changed ? retrievalQuery : "";
  }
  if (answerQuestionInfo && answerQuestionText) {
    const answerQuestion = currentAnswerQuestion.trim();
    const changed = answerQuestion && answerQuestion !== typedQuestion;
    answerQuestionInfo.hidden = !changed;
    answerQuestionText.textContent = changed ? answerQuestion : "";
  }
}

// Chunks the token budget dropped are shown as ordinary cards inside the
// uncited group, badged, rather than buried in a separate details block: "the
// model did not cite it" and "the model never saw it" are different facts.
function withOmittedChunks(sources, chunks, omittedChunks) {
  const omitted = omittedChunks || [];
  return {
    sources: (sources || []).concat(chunksToSources(omitted)),
    chunks: (chunks || []).concat(omitted),
    omittedCitationIds: omitted.map((chunk) => chunk.citation_id).filter(Boolean),
  };
}

function renderSources(sources, chunks, answerText = streamedAnswerText) {
  renderQueryUsedInfo();
  const combined = withOmittedChunks(sources, chunks, currentOmittedChunks);
  const layout = Avatar.layoutSources(combined.sources, mainSourcesView, {
    orderedCitationIds: Avatar.extractOrderedCitationIds(answerText),
    omittedCitationIds: combined.omittedCitationIds,
  });
  renderSourceCards(
    sourcesEl,
    combined.sources,
    combined.chunks,
    currentRetrievalQuery || question.value,
    layout,
    "main-source",
    (patch) => {
      mainSourcesView = { ...mainSourcesView, ...patch };
      renderSources(sources, chunks, answerText);
    },
  );
  renderBudgetNotes(sourcesEl, currentBudgetWarnings, currentOmittedChunks, currentTokenBudget, currentConversationSummary);
  renderBaselineComparison();
}

// Settle the main panel once a stream finishes cleanly: flip to citation order
// and collapse the uncited group. Never called for an aborted or errored stream,
// where the citation set is incomplete.
function completeMainSources(sources, chunks, answerText) {
  mainSourcesView = Avatar.completedSourcesView(mainSourcesView, Avatar.extractOrderedCitationIds(answerText));
  renderSources(sources, chunks, answerText);
}

function renderBaselineComparison() {
  // Server-side mSearch rescoring returns only the reordered list, so there is no
  // baseline to compare — just confirm it ran with a small note.
  msearchRescoreNote.hidden = !(currentMsearchRescoreUsed && currentAnswerSources.length > 0);
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
    renderSourceCards(
      baselineSourcesEl,
      baselineSources,
      currentBaselineChunks,
      currentRetrievalQuery || question.value,
      Avatar.layoutSources(baselineSources, STATIC_SOURCES_VIEW),
      "baseline-source",
    );
  } else {
    baselineSourcesEl.innerHTML = "";
  }
}

conversationMessages?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-copy-scope='conversation']");
  if (!button) {
    return;
  }
  const index = Number(button.closest(".conversation-message")?.dataset.messageIndex);
  const message = ensureSelectedConversation()?.messages?.[index];
  if (!message) {
    return;
  }
  copyAnswerText(message.content || "", message.sources || [], {
    includeSources: button.dataset.copySources === "1",
    statusEl: button.parentElement?.querySelector(".copy-status"),
  });
});

historyDetail?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-copy-scope='history']");
  if (!button || !historyDetailEntry) {
    return;
  }
  const entry = historyDetailEntry;
  const sources =
    entry.sources && entry.sources.length ? entry.sources : chunksToSources(entry.retrieved_chunks || []);
  copyAnswerText(entry.answer || "", sources, {
    includeSources: button.dataset.copySources === "1",
    statusEl: button.parentElement?.querySelector(".copy-status"),
  });
});

answerActions?.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-copy-scope='main']");
  if (!button) {
    return;
  }
  copyAnswerText(streamedAnswerText, currentAnswerSources, {
    includeSources: button.dataset.copySources === "1",
    statusEl: copyAnswerStatus,
  });
});

toggleBaselineBtn.addEventListener("click", () => {
  baselineVisible = !baselineVisible;
  renderBaselineComparison();
});

// Copy support. The clipboard gets the answer as displayed — citation markers
// renumbered to the superscripts the reader saw, model-invented source lists
// gone — optionally followed by a numbered key of the cited sources.
let copyStatusTimer = null;

function showCopyStatus(statusEl, message, isError = false) {
  if (!statusEl) {
    return;
  }
  statusEl.textContent = message;
  statusEl.classList.toggle("copy-status-error", isError);
  window.clearTimeout(copyStatusTimer);
  copyStatusTimer = window.setTimeout(() => {
    statusEl.textContent = "";
    statusEl.classList.remove("copy-status-error");
  }, 2500);
}

async function copyAnswerText(answerText, sources, { includeSources, statusEl }) {
  const text = Avatar.answerForCopy(answerText, sources, { includeSources });
  if (!text) {
    showCopyStatus(statusEl, "Není co kopírovat.", true);
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    showCopyStatus(statusEl, includeSources ? "Zkopírováno se zdroji." : "Zkopírováno.");
  } catch (error) {
    showCopyStatus(statusEl, `Kopírování selhalo: ${error.message}`, true);
  }
}

// The main panel's buttons appear only once there is an answer to copy.
function updateAnswerActions() {
  if (answerActions) {
    answerActions.hidden = !streamedAnswerText.trim();
  }
}

function renderAnswer(text) {
  renderQueryUsedInfo();
  updateAnswerActions();
  answerEl.innerHTML = Avatar.renderMarkdown(text, currentAnswerSources, "main-source");
  updateUsedSourceHighlights(sourcesEl, Avatar.extractCitationIds(text));
}

const CITE_TOGGLE_TITLE = "Zvýraznit místa v odpovědi, kde je zdroj citován";
const SOURCES_PROVISIONAL_ORDER_NOTE =
  "Zdroje jsou zatím řazené podle relevance vyhledávání; po dokončení odpovědi se seřadí podle citací.";

// Top slot of the panel: the provisional-order notice while the answer streams,
// then either the order toggle or — when nothing was cited — the reason why the
// panel did not reorder.
function sourcesOrderControlHtml(layout) {
  if (layout.showNotice) {
    return `<p class="sources-order-note">${escapeHtml(SOURCES_PROVISIONAL_ORDER_NOTE)}</p>`;
  }
  if (layout.showNoCitationsNotice) {
    return `<p class="sources-order-note sources-order-note-warning">Odpověď necituje žádný zdroj.</p>`;
  }
  if (!layout.showOrderToggle) {
    return "";
  }
  const label =
    layout.order === Avatar.CITATION_ORDER ? "Seřadit podle relevance" : "Seřadit podle citací";
  return `<button type="button" class="ghost-button sources-order-toggle">${escapeHtml(label)}</button>`;
}

// Bottom slot: the uncited group's disclosure. Only meaningful in citation order.
function sourcesUncitedControlHtml(layout) {
  if (!layout.showUncitedToggle) {
    return "";
  }
  const label = layout.hiddenCount
    ? `Zobrazit necitované zdroje (${layout.uncitedCount})`
    : "Skrýt necitované";
  return `<button type="button" class="ghost-button sources-uncited-toggle">${escapeHtml(label)}</button>`;
}

/**
 * Render one sources panel.
 *
 * `layout` comes from `Avatar.layoutSources` and carries the whole view
 * decision (order, which cards are visible, whether citation numbers show).
 * `onViewChange` receives a patch for the caller's own view state; panels that
 * have no controls (the baseline column, history) simply omit it.
 */
function renderSourceCards(container, sources, chunks, highlightQuery, layout, idPrefix = "source", onViewChange = null) {
  if (!sources.length) {
    container.textContent = "Žádné zdroje nebyly vráceny.";
    applyCitationHighlights();
    return;
  }
  const highlightTerms = extractHighlightTerms(highlightQuery);
  const chunkById = new Map((chunks || []).map((chunk) => [chunk.chunk_id, chunk]));
  const cards = layout.visible
    .map((entry) => {
      const source = entry.source;
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
      const citationId = entry.citationId;
      // The retrieval id sits with the other diagnostics rather than in the
      // title, where it competed with the citation number the answer shows.
      const scoreLine = [citationId, ...Avatar.sourceScoreParts(source, chunk)].filter(Boolean).join(" · ");
      const isUsed = entry.cited;
      // `cited-source` is the fact (click target, cite toggle); `used-source` is
      // the green, painted only where it tells the cited from the uncited.
      const citedClass = isUsed ? " cited-source" : "";
      const usedClass = isUsed && layout.highlightCited ? " used-source" : "";
      const budgetStatus = chunk?.metadata?.budget_status || "";
      const trimmedBadge = budgetStatus === "trimmed" ? `<span class="source-badge">zkráceno pro prompt</span>` : "";
      // The model never saw this chunk, which is a stronger statement than "did
      // not cite it" — worth its own badge rather than blending into the group.
      const omittedBadge = entry.omitted ? `<span class="source-badge">vynecháno z promptu</span>` : "";
      const originalText = chunk?.metadata?.original_text || "";
      const label = escapeHtml(Avatar.sourceCardLabel(entry, layout.showCitationNumbers));
      // No citation number means no button: it would be an empty disabled
      // control. The whole card stays clickable through `cited-source`.
      const citeButton = label
        ? `<button type="button" class="source-cite-btn" aria-pressed="false" title="${CITE_TOGGLE_TITLE}"${isUsed ? "" : " disabled"}>${label}</button> `
        : "";
      return `
        <article class="source${citedClass}${usedClass}" id="${escapeHtml(idPrefix)}-${escapeHtml(citationId)}" data-citation-id="${escapeHtml(citationId)}">
          <strong>${citeButton}${title} ${trimmedBadge}${omittedBadge}</strong>
          <p>${path}${page}${url}${metaUrl}</p>
          <p class="score">${escapeHtml(scoreLine)}</p>
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
  container.innerHTML = sourcesOrderControlHtml(layout) + cards + sourcesUncitedControlHtml(layout);
  if (onViewChange) {
    container.querySelector(".sources-order-toggle")?.addEventListener("click", () => {
      onViewChange({
        order: layout.order === Avatar.CITATION_ORDER ? Avatar.RETRIEVED_ORDER : Avatar.CITATION_ORDER,
      });
    });
    container.querySelector(".sources-uncited-toggle")?.addEventListener("click", () => {
      onViewChange({ showUncited: layout.hiddenCount > 0 });
    });
  }
  applyCitationHighlights();
}

// The token budget as a subtraction the reader can follow: the context window
// is what the model has, the output reserve comes off the top, and the rest is
// what the prompt is allowed to fill. The old one-line version listed the same
// four numbers in an order that implied no relationship between them.
function tokenBudgetRow(label, value, { kind = "" } = {}) {
  if (value === null || value === undefined) {
    return "";
  }
  const className = kind ? ` class="budget-row-${kind}"` : "";
  return `<tr${className}><th scope="row">${escapeHtml(label)}</th><td>${escapeHtml(formatTokenCount(value))}</td></tr>`;
}

function renderTokenBudgetDetails(tokenBudget, { conversationSummary = "", foldedMessages = 0, className = "" } = {}) {
  const view = Avatar.tokenBudgetView(tokenBudget, { conversationSummary, foldedMessages });
  if (!view) {
    return "";
  }
  const safetyMarginLabel =
    view.safetyMarginPercent !== null
      ? `− bezpečnostní rezerva ${view.safetyMarginPercent} %`
      : "− bezpečnostní rezerva";
  const headline =
    view.totalInput !== null && view.usableInput !== null
      ? `Tokenový rozpočet · ${formatTokenCount(view.totalInput)} z ${formatTokenCount(view.usableInput)} tokenů vstupu${view.inputUsagePercent !== null ? ` (${view.inputUsagePercent} %)` : ""}`
      : "Tokenový rozpočet";

  const chunkCounts = [
    view.usedChunks ? `${view.usedChunks} v promptu` : "",
    view.trimmedChunks ? `${view.trimmedChunks} zkráceno` : "",
    view.omittedChunks ? `${view.omittedChunks} vynecháno` : "",
  ].filter(Boolean);
  const detailsClass = ["budget-details", className].filter(Boolean).join(" ");
  const historyRow = view.historyTokens
    ? tokenBudgetRow("↳ z toho historie konverzace", view.historyTokens, { kind: "subset" })
    : "";
  const foldedNote = view.foldedMessages
    ? `<p class="budget-note-line">Ve shrnutí je ${escapeHtml(view.foldedMessages)} starších zpráv.</p>`
    : "";
  const summaryBlock = view.conversationSummary
    ? `<div class="context-summary-block"><h4>Komprimovaný kontext konverzace</h4><p>${escapeHtml(view.conversationSummary)}</p></div>`
    : "";

  return `
    <details class="${escapeHtml(detailsClass)}">
      <summary>${escapeHtml(headline)}</summary>
      <table class="budget-table">
        <tbody>
          ${tokenBudgetRow("Kontextové okno", view.contextWindow)}
          ${tokenBudgetRow("− rezerva na odpověď", view.reservedOutput)}
          ${view.safetyMargin ? tokenBudgetRow(safetyMarginLabel, view.safetyMargin) : ""}
          ${tokenBudgetRow("= k dispozici pro vstup", view.usableInput, { kind: "subtotal" })}
        </tbody>
        <tbody>
          ${tokenBudgetRow("Prompt bez zdrojů celkem", view.nonSourceTokens)}
          ${historyRow}
          ${tokenBudgetRow("Zdroje odeslané modelu", view.sourceTokens)}
          ${tokenBudgetRow("= vstup celkem", view.totalInput, { kind: "subtotal" })}
        </tbody>
        <tbody>
          ${tokenBudgetRow("Nalezené zdroje před úpravou", view.retrievedSourceTokens)}
        </tbody>
      </table>
      ${chunkCounts.length ? `<p class="budget-note-line">Zdroje: ${escapeHtml(chunkCounts.join(" · "))}.</p>` : ""}
      ${view.summaryUsed ? `<p class="budget-note-line">Historie konverzace je poslána jako shrnutí.</p>` : ""}
      ${foldedNote}
      ${summaryBlock}
    </details>
  `;
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
  const tokenBudgetHtml = renderTokenBudgetDetails(tokenBudget);
  if (tokenBudgetHtml) {
    parts.push(tokenBudgetHtml);
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
    // The chunks themselves render as badged cards in the uncited group; this
    // only says how many the budget dropped.
    parts.push(`
      <p class="budget-note-line">Token budget vynechal ${omittedChunks.length} nalezených chunků z promptu.</p>
    `);
  }
  if (parts.length) {
    container.insertAdjacentHTML("afterbegin", parts.join(""));
  }
}

function updateUsedSourceHighlights(container, usedCitationIds) {
  const cards = Array.from(container.querySelectorAll(".source"));
  const citedCount = cards.filter((card) => usedCitationIds.has(card.dataset.citationId || "")).length;
  // Same rule as the rendered layout: the green only means something while some
  // card on screen is still uncited.
  const highlightCited = citedCount > 0 && citedCount < cards.length;
  for (const card of cards) {
    const citationId = card.dataset.citationId || "";
    const isUsed = usedCitationIds.has(citationId);
    card.classList.toggle("cited-source", isUsed);
    card.classList.toggle("used-source", isUsed && highlightCited);
    // A card can become cited mid-stream, so its toggle is enabled here rather
    // than only at render time.
    const toggle = card.querySelector(".source-cite-btn");
    if (toggle) {
      toggle.disabled = !isUsed;
    }
  }
  applyCitationHighlights();
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
  const sourceSelector = sourceCardSelector(citationId);
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

// The reverse of pulseSourceCardFromCitation: clicking a source card lights up
// every superscript in the answer that cites it. Each scope pairs a panel of
// source cards with the answer those cards belong to; the conversation and
// history entries come first because their panels sit inside their own dialogs.
const CITATION_SCOPES = [
  {
    name: "conversation",
    sourcesSelector: ".conversation-sources-panel",
    answerSelector: "#conversationMessages",
  },
  { name: "history", sourcesSelector: "#historySources", answerSelector: ".history-answer" },
  { name: "main", sourcesSelector: ".sources-panel", answerSelector: "#answer" },
];

function escapeSelectorValue(value) {
  return typeof CSS !== "undefined" && CSS.escape ? CSS.escape(value) : value;
}

function sourceCardSelector(citationId) {
  return `.source[data-citation-id="${escapeSelectorValue(citationId)}"]`;
}

function citationScopeForCard(card) {
  return CITATION_SCOPES.find((scope) => card.closest(scope.sourcesSelector)) || null;
}

function citationMarkers(scope, citationId) {
  const answerRoot = document.querySelector(scope.answerSelector);
  if (!answerRoot) {
    return [];
  }
  return Array.from(
    answerRoot.querySelectorAll(`.footnote-ref a[data-citation-id="${escapeSelectorValue(citationId)}"]`),
  );
}

// Repaints the sticky highlight from activeCitation. Safe to call after any
// render — it clears first, and drops the selection if the card it pointed at is
// gone (new answer, closed dialog, source no longer cited).
function applyCitationHighlights() {
  for (const marker of document.querySelectorAll(".footnote-ref a.citation-active")) {
    marker.classList.remove("citation-active");
  }
  for (const card of document.querySelectorAll(".source.active-source")) {
    card.classList.remove("active-source");
    card.querySelector(".source-cite-btn")?.setAttribute("aria-pressed", "false");
  }
  if (!activeCitation) {
    return;
  }
  const scope = CITATION_SCOPES.find((entry) => entry.name === activeCitation.scope);
  const card = scope
    ? document.querySelector(`${scope.sourcesSelector} ${sourceCardSelector(activeCitation.citationId)}`)
    : null;
  if (!card || !card.classList.contains("cited-source")) {
    activeCitation = null;
    return;
  }
  card.classList.add("active-source");
  card.querySelector(".source-cite-btn")?.setAttribute("aria-pressed", "true");
  for (const marker of citationMarkers(scope, activeCitation.citationId)) {
    marker.classList.add("citation-active");
  }
}

function setActiveCitation(next) {
  activeCitation = next;
  applyCitationHighlights();
}

function isCitationMarkerVisible(marker, answerRoot) {
  const rect = marker.getBoundingClientRect();
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
  if (rect.bottom <= 0 || rect.top >= viewportHeight) {
    return false;
  }
  // The conversation transcript and history detail scroll inside their own box,
  // so a marker can sit in the viewport yet be clipped out of its container.
  const bounds = answerRoot.getBoundingClientRect();
  return rect.bottom > bounds.top && rect.top < bounds.bottom;
}

function scrollToFirstCitationMarker(scope, citationId) {
  const answerRoot = document.querySelector(scope.answerSelector);
  const markers = citationMarkers(scope, citationId);
  if (!answerRoot || !markers.length) {
    return;
  }
  if (markers.some((marker) => isCitationMarkerVisible(marker, answerRoot))) {
    return;
  }
  markers[0].scrollIntoView({ behavior: "smooth", block: "center" });
}

function toggleCitationHighlightFromSource(event) {
  const card = event.target.closest(".source");
  if (!card) {
    // Empty space inside a sources panel clears the highlight. Clicks elsewhere
    // leave it alone, so it survives scrolling and selecting text in the answer.
    if (activeCitation && CITATION_SCOPES.some((scope) => event.target.closest(scope.sourcesSelector))) {
      setActiveCitation(null);
    }
    return;
  }
  // Let the card's own controls work, and ignore the click that ends a text
  // selection in the excerpt.
  if (event.target.closest("a, summary") || window.getSelection()?.isCollapsed === false) {
    return;
  }
  const citationId = card.dataset.citationId || "";
  const scope = citationScopeForCard(card);
  if (!citationId || !scope || !card.classList.contains("cited-source")) {
    return;
  }
  const isActive = activeCitation?.scope === scope.name && activeCitation.citationId === citationId;
  setActiveCitation(isActive ? null : { scope: scope.name, citationId });
  if (!isActive) {
    scrollToFirstCitationMarker(scope, citationId);
  }
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
  return saveEntryListSafely(
    CONVERSATION_STORAGE_KEY,
    entries,
    compactStoredConversation,
    "conversation entries",
  );
}

function createConversation() {
  const conversations = getConversationEntries();
  const conversation = {
    id: Date.now(),
    title: "Nová konverzace",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    conversation_summary: "",
    // How many leading messages the server has already folded into
    // conversation_summary. They stay on screen but are no longer uploaded, so
    // the running context shrinks instead of growing forever.
    conversation_compacted_through: 0,
    rewrite_query_for_retrieval: true,
    // New conversations inherit the main page's current settings, then own them.
    settings: currentMainSettings(),
    messages: [],
  };
  conversations.unshift(conversation);
  const savedConversations = setConversationEntries(conversations);
  selectedConversationId = savedConversations.some((entry) => entry.id === conversation.id)
    ? conversation.id
    : savedConversations[0]?.id ?? conversation.id;
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

function conversationRewriteEnabled(conversation) {
  return conversation?.rewrite_query_for_retrieval !== false;
}

function updateConversation(updatedConversation) {
  const conversations = getConversationEntries();
  const nextConversations = conversations.map((entry) =>
    entry.id === updatedConversation.id ? updatedConversation : entry,
  );
  nextConversations.sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
  const savedConversations = setConversationEntries(nextConversations);
  selectedConversationId = updatedConversation.id;
  if (!savedConversations.some((entry) => entry.id === selectedConversationId)) {
    selectedConversationId = savedConversations[0]?.id ?? null;
  }
  return storageSaveSucceeded.get(CONVERSATION_STORAGE_KEY) === true;
}

function deleteSelectedConversation() {
  const conversations = getConversationEntries();
  if (!conversations.length || selectedConversationId === null) {
    return;
  }
  const remaining = conversations.filter((entry) => entry.id !== selectedConversationId);
  const savedConversations = setConversationEntries(remaining);
  selectedConversationId = savedConversations[0]?.id ?? null;
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

// ---------------------------------------------------------------------------
// Per-conversation settings (WP / prompt / provider+model / context window /
// placeholders). Each conversation owns its settings; the main page is left
// untouched. While the conversation modal is open the global settings state
// represents the active conversation, so the existing prompt/placeholder/model
// machinery resolves everything; the main page's own settings are backed up on
// open and restored on close.
// ---------------------------------------------------------------------------

// Snapshot the current global settings state into a plain settings object that
// mirrors the chat-request fields a conversation owns.
function captureSettingsSnapshot() {
  const activePrompt = activePromptPresetMetadata();
  return {
    wp_id: activeWpId,
    prompt_preset_id: activePromptPresetId,
    prompt_preset_name: activePrompt.name,
    prompt_preset_note: activePrompt.note,
    system_prompt: systemPrompt.value,
    user_prompt_template: userPromptTemplate.value,
    selections: { ...placeholderSelections },
    placeholder_defs: effectivePlaceholderDefsForRequest(),
    llm_provider: llmProvider.value,
    model: selectedModelValue(),
    msearch_collection: msearchCollection.value,
    context_window_tokens: nullableInteger(contextWindowTokens.value),
    reasoning_effort: reasoningEffort?.value || "",
  };
}

// The main page's settings: the backup taken when the modal opened, or the live
// state if the modal is not open. Used to seed new conversations and as a
// fallback for conversations saved before this feature existed.
function currentMainSettings() {
  return mainSettingsBackup || captureSettingsSnapshot();
}

function conversationSettingsFor(conversation) {
  return (conversation && conversation.settings) || currentMainSettings();
}

// Apply a settings object onto the global state. Reused for both applying a
// conversation (placeholders render into the conversation container) and
// restoring the main page (placeholders render into the main container). Mirrors
// the relevant subset of applyHistoryEntryToForm without touching retrieval
// controls or the question field.
function applySettingsToGlobals(settings) {
  const s = settings || {};
  const providerValue = normalizeProviderId(s.llm_provider || llmProvider.value || "");
  if (providerValue) {
    loadProviderValues(providerValue, { preferStored: true });
  }
  activeWpId = resolveWpId(s.wp_id);
  wpSelect.value = activeWpId;
  loadPredefinedQuestions(activeWpId);
  populateMsearchCollections(s.msearch_collection || wpDefaultCollectionMsearchId(getWpConfig(activeWpId)));
  const savedPromptId = promptPresetIdFromSettings(s);
  if (promptPresetExists(savedPromptId)) {
    applyPromptPresetById(savedPromptId);
  } else {
    applyPromptPresetById(defaultPromptPresetId(activeWpId));
  }
  // Re-apply saved prompt-text overrides (which can change the active tokens),
  // then re-render controls before restoring the saved selection values.
  systemPrompt.value = s.system_prompt || systemPrompt.value;
  userPromptTemplate.value = s.user_prompt_template || userPromptTemplate.value;
  renderPlaceholderControls();
  applyPlaceholderSelections(s.selections);
  updatePromptTemplateWarning();
  refreshModelOptions(appSettings);
  const modelValue = s.model || "";
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
  if (s.context_window_tokens != null) {
    setContextWindowTokensValue(s.context_window_tokens);
  }
  updateModelContextWindowNote();
  refreshReasoningEffortOptions();
  if (reasoningEffort && s.reasoning_effort !== undefined) {
    const wanted = String(s.reasoning_effort || "");
    reasoningEffort.value = Array.from(reasoningEffort.options).some((option) => option.value === wanted)
      ? wanted
      : REASONING_DEFAULT_VALUE;
  }
}

// Apply a WP for conversation mode: WP + its default collection + default
// prompt, without touching the shared retrieval controls (unlike selectWp).
function applyConvWp(wpId) {
  activeWpId = resolveWpId(wpId);
  wpSelect.value = activeWpId;
  loadPredefinedQuestions(activeWpId);
  populateMsearchCollections(wpDefaultCollectionMsearchId(getWpConfig(activeWpId)));
  applyPromptPresetById(defaultPromptPresetId(activeWpId));
}

// Mirror the (single-sourced) main control option lists + values into the
// compact conversation controls, avoiding duplicate population logic.
function mirrorConversationControls() {
  if (convWpSelect) {
    convWpSelect.innerHTML = wpSelect.innerHTML;
    convWpSelect.value = wpSelect.value;
  }
  if (convPromptSelect) {
    convPromptSelect.innerHTML = activePromptPreset.innerHTML;
    convPromptSelect.value = activePromptPreset.value;
  }
  if (convProvider) {
    convProvider.innerHTML = llmProvider.innerHTML;
    convProvider.value = llmProvider.value;
  }
  if (convModel) {
    convModel.innerHTML = model.innerHTML;
    convModel.value = model.value;
  }
  if (convCustomModel) {
    convCustomModel.value = customModel.value;
  }
  updateConvCustomModelVisibility();
}

function updateConvCustomModelVisibility() {
  if (!convCustomModelField) {
    return;
  }
  const showCustom = convModel?.value === CUSTOM_MODEL_VALUE && customModelAllowed();
  convCustomModelField.hidden = !showCustom;
}

function resetConvContextWindowToSelectedModel() {
  if (!convContextWindowTokens) {
    return;
  }
  const nextWindow = selectedModelContextWindow() ?? defaultContextWindowTokens();
  convContextWindowTokens.value = nextWindow ?? "";
}

// Context-window note for the conversation bar: compares the conversation's own
// context window against the conversation model's known maximum.
function updateConvModelContextWindowNote() {
  if (!convModelContextWindowNote) {
    return;
  }
  const knownWindow = selectedModelContextWindow();
  const currentWindow = nullableInteger(convContextWindowTokens?.value);
  convModelContextWindowNote.classList.remove("warning");
  if (knownWindow) {
    if (currentWindow && currentWindow > knownWindow) {
      convModelContextWindowNote.classList.add("warning");
      convModelContextWindowNote.textContent =
        `Známé maximum pro tento model: ${formatTokenCount(knownWindow)} tokenů. `
        + `Aktuálně používáte ${formatTokenCount(currentWindow)} tokenů, takže se kontext nemusí vejít.`;
      return;
    }
    const suffix =
      currentWindow && currentWindow !== knownWindow
        ? ` Aktuálně používáte ${formatTokenCount(currentWindow)} tokenů.`
        : "";
    convModelContextWindowNote.textContent = `Známé maximum pro tento model: ${formatTokenCount(knownWindow)} tokenů.${suffix}`;
    return;
  }
  convModelContextWindowNote.textContent =
    `Pro tento model nemáme uložené maximum. Výchozí hodnota aplikace: ${formatTokenCount(defaultContextWindowTokens())} tokenů.`;
}

// Apply a conversation's settings to the global state and reflect them into the
// conversation settings bar. Called only on selection changes (open, switch,
// new), never during streaming re-renders.
function applyConversationSettings(conversation) {
  const s = conversationSettingsFor(conversation);
  applySettingsToGlobals(s);
  if (convContextWindowTokens) {
    const ctx = s.context_window_tokens ?? nullableInteger(contextWindowTokens.value);
    convContextWindowTokens.value = ctx ?? "";
  }
  mirrorConversationControls();
  updateConvModelContextWindowNote();
}

// Persist the current global state (plus the conversation context-window input)
// onto the active conversation's settings, without bumping updatedAt or
// reordering the list under the user.
function persistActiveConversationSettings() {
  if (!conversationSettingsActive || selectedConversationId === null) {
    return;
  }
  const entries = getConversationEntries();
  if (!entries.some((entry) => entry.id === selectedConversationId)) {
    return;
  }
  const snapshot = captureSettingsSnapshot();
  snapshot.context_window_tokens = nullableInteger(convContextWindowTokens?.value);
  const next = entries.map((entry) =>
    entry.id === selectedConversationId ? { ...entry, settings: snapshot } : entry,
  );
  setConversationEntries(next);
}

// Select a conversation and load its settings (used by list clicks and after
// create/delete). Keeps settings application out of the streaming render path.
function selectConversation(id) {
  selectedConversationId = id;
  // Whatever is stored is already final; let the panel settle itself on render.
  conversationSourcesView = null;
  if (conversationSettingsActive) {
    applyConversationSettings(ensureSelectedConversation());
  }
  renderConversationWorkspace();
}

function openConversationWorkspace() {
  mainSettingsBackup = captureSettingsSnapshot();
  conversationSettingsActive = true;
  activePlaceholderContainer = convPlaceholderControls;
  const storedConversations = getConversationEntries();
  if (storedConversations.length) {
    // Apply the current compact representation to existing conversations too,
    // rather than waiting for each one to receive another message.
    setConversationEntries(storedConversations);
  }
  renderConversationWorkspace();
  refreshConversationStorageStatus();
  applyConversationSettings(ensureSelectedConversation());
  conversationDialog.showModal();
}

function exportLegacyHistory() {
  const raw = localStorage.getItem(LEGACY_HISTORY_STORAGE_KEY) || "";
  if (!raw) {
    refreshConversationStorageStatus();
    return;
  }
  const url = URL.createObjectURL(new Blob([raw], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `czdemos4ai-history-legacy-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function deleteLegacyHistory() {
  const raw = localStorage.getItem(LEGACY_HISTORY_STORAGE_KEY) || "";
  if (!raw) {
    refreshConversationStorageStatus();
    return;
  }
  const confirmed = window.confirm(
    "Smazat starou místní historii? Tato data už aplikace nezobrazuje. "
    + "Pokud je chcete zachovat, nejdříve použijte Exportovat starou historii.",
  );
  if (!confirmed) {
    return;
  }
  localStorage.removeItem(LEGACY_HISTORY_STORAGE_KEY);
  conversationStorageFailure = "";
  refreshConversationStorageStatus();
}

// Restore the main page's own settings after the conversation modal closes.
function restoreMainSettings() {
  conversationSettingsActive = false;
  activePlaceholderContainer = placeholderControls;
  if (!mainSettingsBackup) {
    return;
  }
  applySettingsToGlobals(mainSettingsBackup);
  mainSettingsBackup = null;
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
      selectConversation(Number(item.dataset.conversationId));
    });
  }
}

function renderConversationDetail(conversation) {
  const messages = conversation?.messages || [];
  const latestAssistant = [...messages].reverse().find((message) => message.role === "assistant");
  const latestSources =
    latestAssistant?.sources?.length ? latestAssistant.sources : chunksToSources(latestAssistant?.retrieved_chunks || []);
  const latestChunks = latestAssistant?.retrieved_chunks || [];
  if (conversationRewriteQuery) {
    conversationRewriteQuery.checked = conversationRewriteEnabled(conversation);
  }

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
      .map((message, index) => renderConversationMessage(message, index))
      .join("");
    conversationMessages.scrollTop = conversationMessages.scrollHeight;
  }

  renderConversationSourceCards(latestAssistant, latestSources, latestChunks);
  renderConversationRetrievalInfo(latestAssistant);
}

// Same panel machinery as the main page, driven by conversationSourcesView so
// the two cannot drift apart. Split out so the view toggles can re-render just
// the source column instead of the whole conversation detail.
function renderConversationSourceCards(latestAssistant, sources, chunks) {
  const combined = withOmittedChunks(sources, chunks, latestAssistant?.omitted_chunks || []);
  const orderedCitationIds = Avatar.extractOrderedCitationIds(latestAssistant?.content || "");
  if (!conversationSourcesView) {
    conversationSourcesView = Avatar.completedSourcesView(
      Avatar.createSourcesView({ canFlip: Boolean(latestAssistant) }),
      orderedCitationIds,
    );
  }
  const layout = Avatar.layoutSources(combined.sources, conversationSourcesView, {
    orderedCitationIds,
    omittedCitationIds: combined.omittedCitationIds,
  });
  renderSourceCards(
    conversationSources,
    combined.sources,
    combined.chunks,
    conversationRetrievalQuery(latestAssistant, conversationQuestion.value),
    layout,
    "conversation-source",
    (patch) => {
      conversationSourcesView = { ...conversationSourcesView, ...patch };
      renderConversationSourceCards(latestAssistant, sources, chunks);
    },
  );
}

function conversationOriginalQuestion(message, fallback = "") {
  return message?.original_question || message?.question || fallback || "";
}

function conversationRetrievalQuery(message, fallback = "") {
  return message?.retrieval_query || conversationOriginalQuestion(message, fallback);
}

function renderConversationRetrievalInfo(message) {
  if (!conversationRetrievalInfo) {
    return;
  }
  if (!message) {
    conversationRetrievalInfo.hidden = true;
    conversationRetrievalInfo.innerHTML = "";
    return;
  }
  const originalQuestion = conversationOriginalQuestion(message);
  const retrievalQuery = conversationRetrievalQuery(message);
  const rewriteView = Avatar.conversationQueryRewriteView(message);
  if ((!originalQuestion && !retrievalQuery) || (!rewriteView.showQueries && !rewriteView.skippedMessage)) {
    conversationRetrievalInfo.hidden = true;
    conversationRetrievalInfo.innerHTML = "";
    return;
  }
  conversationRetrievalInfo.hidden = false;
  if (!rewriteView.showQueries) {
    conversationRetrievalInfo.innerHTML = `<p>${escapeHtml(rewriteView.skippedMessage)}</p>`;
    return;
  }
  conversationRetrievalInfo.innerHTML = `
    <div class="conversation-retrieval-info-row">
      <span>Původní dotaz</span>
      <strong>${escapeHtml(originalQuestion || retrievalQuery)}</strong>
    </div>
    <div class="conversation-retrieval-info-row">
      <span>Dotaz pro vyhledávání</span>
      <strong>${escapeHtml(retrievalQuery || originalQuestion)}</strong>
    </div>
    ${rewriteView.rewritten ? `<p>Dotaz byl upraven pro lepší vyhledání zdrojů.</p>` : ""}
    ${rewriteView.unchangedMessage ? `<p>${escapeHtml(rewriteView.unchangedMessage)}</p>` : ""}
  `;
}

function retrievalInfoFromEvent(data = {}, fallbackQuestion = "", previous = null) {
  const originalQuestion = data.original_question || data.question || previous?.original_question || fallbackQuestion || "";
  const retrievalQuery = data.retrieval_query || previous?.retrieval_query || originalQuestion;
  const rewritten =
    data.retrieval_query_was_rewritten === true
      ? true
      : data.retrieval_query_was_rewritten === false
        ? false
        : previous?.retrieval_query_was_rewritten === true;
  return {
    original_question: originalQuestion,
    retrieval_query: retrievalQuery,
    retrieval_query_was_rewritten: rewritten,
    retrieval_query_rewrite_attempted:
      data.retrieval_query_rewrite_attempted === true
        ? true
        : data.retrieval_query_rewrite_attempted === false
          ? false
          : previous?.retrieval_query_rewrite_attempted === true,
    retrieval_query_rewrite_skip_reason:
      data.retrieval_query_rewrite_skip_reason ?? previous?.retrieval_query_rewrite_skip_reason ?? null,
  };
}

function renderConversationMessage(message, index = 0) {
  const roleLabel = message.role === "assistant" ? "Avatar" : "Ty";
  const messageClass = message.role === "assistant" ? "assistant" : "user";
  const body =
    message.role === "assistant"
      ? Avatar.renderMarkdown(message.content || "", message.sources || [], "conversation-source")
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
  const reasoningBlock =
    message.role === "assistant" && (message.reasoning || "").trim()
      ? `<details class="reasoning-panel"${message.reasoning_streaming ? " open" : ""}>
          <summary>Uvažování modelu</summary>
          <pre class="reasoning-text">${escapeHtml(message.reasoning)}</pre>
        </details>`
      : "";
  const copyActions =
    message.role === "assistant" && (message.content || "").trim()
      ? `<div class="answer-actions">
          <button type="button" class="ghost-button" data-copy-scope="conversation">Kopírovat odpověď</button>
          <button type="button" class="ghost-button" data-copy-scope="conversation" data-copy-sources="1">Kopírovat se zdroji</button>
          <span class="copy-status" role="status" aria-live="polite"></span>
        </div>`
      : "";
  return `
    <article class="conversation-message ${messageClass}" data-message-index="${index}">
      <div class="conversation-message-label">${roleLabel}</div>
      ${reasoningBlock}
      <div class="conversation-message-body">${body}</div>
      ${budgetWarnings}
      ${contextStatus}
      ${copyActions}
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
  const foldedMessages = Number(message?.conversation_compacted_through) || 0;
  const compressionText = foldedMessages
    ? `${foldedMessages} starších zpráv ve shrnutí`
    : budget?.conversation_summary_used || summary
      ? "komprese zapnutá"
      : "bez komprese";
  const visibleParts = [sourceText, compressionText];
  if (trimmedChunks > 0) {
    visibleParts.push(`${trimmedChunks} zkráceno`);
  }
  const budgetView = Avatar.tokenBudgetView(budget, { foldedMessages, conversationSummary: summary });
  const totalInputTokens = budgetView?.totalInput ?? null;
  const usagePercent = budgetView?.windowUsagePercent ?? null;
  if (totalInputTokens !== null) {
    visibleParts.unshift(`${totalInputTokens} tokenů vstup`);
  }

  const budgetDetails = renderTokenBudgetDetails(budget, {
    conversationSummary: summary,
    foldedMessages,
    className: "conversation-context-details",
  });

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
      ${budgetDetails}
    </div>
  `;
}

// In-flight conversation request, aborted by the conversation cancel button.
let activeConversationController = null;

async function submitConversationTurn() {
  const prompt = conversationQuestion.value.trim();
  if (!prompt) {
    return;
  }
  const controller = new AbortController();
  const turnId = newAnalyticsId();
  activeConversationController = controller;
  let requestFailed = false;
  if (conversationRequestStatus) {
    conversationRequestStatus.textContent = "";
    conversationRequestStatus.classList.remove("error");
  }
  conversationSubmitButton.disabled = true;
  if (conversationCancelButton) {
    conversationCancelButton.hidden = false;
    conversationCancelButton.disabled = false;
  }
  const storedConversation = ensureSelectedConversation();
  const cleanedMessages = Avatar.removeLegacyTokenBudgetRejectedTurns(storedConversation.messages);
  const conversation =
    cleanedMessages.length === storedConversation.messages.length
      ? storedConversation
      : { ...storedConversation, messages: cleanedMessages, updatedAt: new Date().toISOString() };
  if (conversation !== storedConversation) {
    updateConversation(conversation);
  }
  const rewriteQueryForRetrieval = conversationRewriteEnabled(conversation);
  const userMessage = {
    role: "user",
    content: prompt,
    request_turn_id: turnId,
    createdAt: new Date().toISOString(),
  };
  const workingConversation = {
    ...conversation,
    title: conversation.messages.length ? conversation.title : shortenText(prompt, 64),
    updatedAt: new Date().toISOString(),
    rewrite_query_for_retrieval: rewriteQueryForRetrieval,
    messages: [...conversation.messages, userMessage],
  };
  const turnSaved = updateConversation(workingConversation);
  if (!turnSaved) {
    renderConversationWorkspace();
    refreshConversationStorageStatus();
    conversationSubmitButton.disabled = false;
    if (conversationCancelButton) {
      conversationCancelButton.hidden = true;
    }
    activeConversationController = null;
    return;
  }
  renderConversationWorkspace();
  conversationQuestion.value = "";

  let assistantText = "";
  let assistantReasoning = "";
  // Reasoning deltas and answer tokens both grow the same in-progress assistant
  // message, so they share one writer rather than two copies that drift.
  const upsertStreamingAssistantMessage = ({ reasoningStreaming }) => {
    const liveConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id);
    if (!liveConversation) {
      return;
    }
    const messages = [...liveConversation.messages];
    const lastMessage = messages[messages.length - 1];
    const streamed = {
      content: assistantText,
      reasoning: assistantReasoning,
      reasoning_streaming: reasoningStreaming,
      sources: latestSources,
      retrieved_chunks: latestChunks,
    };
    if (lastMessage?.role === "assistant") {
      Object.assign(lastMessage, streamed, latestRetrievalInfo);
    } else {
      messages.push({
        role: "assistant",
        question: prompt,
        ...latestRetrievalInfo,
        ...streamed,
        settings: sanitizedPayload,
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
      rewrite_query_for_retrieval: rewriteQueryForRetrieval,
      updatedAt: new Date().toISOString(),
      messages,
    });
    renderConversationWorkspace();
  };
  const clearStreamingReasoningFlag = () => {
    const liveConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id);
    const lastMessage = liveConversation?.messages?.[liveConversation.messages.length - 1];
    if (!lastMessage?.reasoning_streaming) {
      return;
    }
    const messages = [...liveConversation.messages];
    messages[messages.length - 1] = { ...lastMessage, reasoning_streaming: false };
    updateConversation({ ...liveConversation, messages });
    renderConversationWorkspace();
  };
  let latestSources = [];
  let latestChunks = [];
  let latestRetrievalInfo = retrievalInfoFromEvent({}, prompt);
  // Build the payload from the conversation's own settings rather than the live
  // main-page controls, so each turn uses the settings this conversation owns.
  const convSettings = conversationSettingsFor(conversation);
  const compactedThrough = Number(conversation.conversation_compacted_through) || 0;
  const payload = buildRequestPayload({
    question: prompt,
    conversation_summary: conversation.conversation_summary || null,
    rewrite_query_for_retrieval: rewriteQueryForRetrieval,
    conversation_history: conversation.messages.slice(compactedThrough).map((message) => ({
      role: message.role,
      content: message.content,
    })),
    wp_id: convSettings.wp_id,
    prompt_preset_id: convSettings.prompt_preset_id,
    prompt_preset_name: convSettings.prompt_preset_name,
    system_prompt: promptOverride(convSettings.system_prompt, appSettings.prompt_defaults?.system_prompt),
    user_prompt_template: promptOverride(convSettings.user_prompt_template, appSettings.prompt_defaults?.user_prompt_template),
    selections: { ...(convSettings.selections || {}) },
    placeholder_defs: convSettings.placeholder_defs || {},
    llm_provider: convSettings.llm_provider,
    model: convSettings.model,
    llm_base_url: nullableString(selectedProviderBaseUrl(convSettings.llm_provider)),
    llm_api_key: nullableString(selectedProviderApiKey(convSettings.llm_provider)),
    msearch_collection: convSettings.msearch_collection,
    context_window_tokens: convSettings.context_window_tokens,
    reasoning_effort: nullableString(convSettings.reasoning_effort),
  });
  const sanitizedPayload = {
    ...sanitizeHistorySettings(payload),
    prompt_preset_note: promptPresetNoteFromSettings(convSettings),
  };

  try {
    // A new turn puts the panel back in retrieved order until the answer settles.
    conversationSourcesView = Avatar.createSourcesView();
    const handleConversationSources = (data) => {
      latestRetrievalInfo = retrievalInfoFromEvent(data, prompt, latestRetrievalInfo);
      latestChunks = data.retrieved_chunks || [];
      latestSources = data.sources || chunksToSources(latestChunks);
      const liveConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id) || workingConversation;
      const messages = [...liveConversation.messages];
      const placeholderAssistant = messages[messages.length - 1];
      if (placeholderAssistant?.role === "assistant") {
        placeholderAssistant.content = assistantText;
        placeholderAssistant.sources = latestSources;
        placeholderAssistant.retrieved_chunks = latestChunks;
        Object.assign(placeholderAssistant, latestRetrievalInfo);
      } else {
        messages.push({
          role: "assistant",
          question: prompt,
          ...latestRetrievalInfo,
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
        rewrite_query_for_retrieval: rewriteQueryForRetrieval,
        updatedAt: new Date().toISOString(),
        messages,
      });
      renderConversationWorkspace();
    };
    await chatRequest(payload, {
      onStatus(data) {
        if (conversationRequestStatus) {
          conversationRequestStatus.textContent = Avatar.requestStatusMessage(data.phase);
        }
      },
      onPreliminarySources(data) {
        if (conversationRequestStatus) {
          conversationRequestStatus.textContent = "";
        }
        handleConversationSources(data);
      },
      onSources(data) {
        if (conversationRequestStatus) {
          conversationRequestStatus.textContent = "";
        }
        handleConversationSources(data);
      },
      onReasoning(delta) {
        assistantReasoning += delta;
        // The trace arrives before the answer does, so this is what creates the
        // assistant bubble on a reasoning model — with `reasoning_streaming` set
        // so the panel renders open until the first answer token clears it.
        upsertStreamingAssistantMessage({ reasoningStreaming: true });
      },
      onToken(token) {
        assistantText += token;
        upsertStreamingAssistantMessage({ reasoningStreaming: false });
      },
      onDone(data) {
        latestRetrievalInfo = retrievalInfoFromEvent(data, prompt, latestRetrievalInfo);
        const liveConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id) || workingConversation;
        const messages = [...liveConversation.messages];
        const assistantMessage = {
          role: "assistant",
          question: prompt,
          ...latestRetrievalInfo,
          content: data.answer || assistantText,
          settings: sanitizedPayload,
          sources: data.sources || latestSources,
          retrieved_chunks: data.retrieved_chunks || latestChunks,
          omitted_chunks: data.omitted_chunks || [],
          token_budget: data.token_budget || null,
          chunk_budget_warnings: data.chunk_budget_warnings || [],
          conversation_summary: data.conversation_summary || null,
          reasoning: data.reasoning || assistantReasoning,
          reasoning_streaming: false,
          conversation_compacted_through: compactedThrough + (Number(data.conversation_folded_message_count) || 0),
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
        conversationSourcesView = Avatar.completedSourcesView(
          conversationSourcesView,
          Avatar.extractOrderedCitationIds(assistantMessage.content || ""),
        );
        // The server folded this many of the messages we uploaded, so stop
        // uploading them. The marker only ever moves forward.
        const foldedNow = Number(data.conversation_folded_message_count) || 0;
        updateConversation({
          ...liveConversation,
          conversation_summary: data.conversation_summary || liveConversation.conversation_summary || "",
          conversation_compacted_through: compactedThrough + foldedNow,
          rewrite_query_for_retrieval: rewriteQueryForRetrieval,
          updatedAt: new Date().toISOString(),
          messages,
        });
        renderConversationWorkspace();
      },
    }, { signal: controller.signal, turnId });
  } catch (error) {
    if (error.name === "AbortError") {
      return;
    }
    requestFailed = true;
    const failedConversation = getConversationEntries().find((entry) => entry.id === workingConversation.id) || workingConversation;
    const tokenBudgetRejected = Avatar.isTokenBudgetErrorDetail(error.detail);
    if (tokenBudgetRejected) {
      updateConversation({
        ...failedConversation,
        title: conversation.messages.length ? failedConversation.title : conversation.title,
        updatedAt: new Date().toISOString(),
        rewrite_query_for_retrieval: rewriteQueryForRetrieval,
        messages: Avatar.rollbackRejectedTurn(failedConversation.messages, turnId),
      });
      if (!conversationQuestion.value.trim()) {
        conversationQuestion.value = prompt;
      }
    } else {
      updateConversation({
        ...failedConversation,
        updatedAt: new Date().toISOString(),
        rewrite_query_for_retrieval: rewriteQueryForRetrieval,
        messages: [
          ...failedConversation.messages,
          {
            role: "assistant",
            question: prompt,
            ...latestRetrievalInfo,
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
    }
    renderConversationWorkspace();
    if (conversationRequestStatus) {
      conversationRequestStatus.textContent = error.message;
      conversationRequestStatus.classList.add("error");
    }
  } finally {
    if (activeConversationController === controller) {
      activeConversationController = null;
    }
    // An aborted or failed stream never reaches `onDone`, and the flag is
    // stored with the message — leave it set and the panel stays wedged open
    // for the life of the conversation.
    clearStreamingReasoningFlag();
    if (conversationRequestStatus && !requestFailed) {
      conversationRequestStatus.textContent = "";
      conversationRequestStatus.classList.remove("error");
    }
    conversationSubmitButton.disabled = false;
    if (conversationCancelButton) {
      conversationCancelButton.hidden = true;
    }
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
    original_question: entry.original_question || entry.question,
    retrieval_query: entry.retrieval_query || entry.settings?.retrieval_query || entry.question,
    use_retrieval_query_for_answer: Boolean(
      entry.use_retrieval_query_for_answer ?? entry.settings?.use_retrieval_query_for_answer,
    ),
    query_transform_action_id: entry.query_transform_action_id || null,
    mode: entry.mode,
    answer: entry.answer,
    sourceCount: entry.sourceCount,
    // Optional per-entry note; editable in the detail pane and shared with the
    // entry when it is pushed to /shared-history.
    note: "",
    settings: sanitizeHistorySettings(entry.settings || {}),
    // Store source name + link + score, but not the (large) snippet text.
    retrieved_chunks: (entry.retrieved_chunks || []).map(stripStoredChunkText),
    omitted_chunks: (entry.omitted_chunks || []).map(stripStoredChunkText),
    token_budget: entry.token_budget || null,
    chunk_budget_warnings: entry.chunk_budget_warnings || [],
    conversation_summary: entry.conversation_summary || null,
    sources: entry.sources || [],
    model_used: entry.model_used || null,
    upstream_model: entry.upstream_model || null,
    response_time_seconds: entry.response_time_seconds ?? null,
    createdAt: new Date().toISOString(),
  });
  const trimmed = history.slice(0, MAX_STORED_HISTORY_ENTRIES);
  const savedHistory = saveEntryListSafely(
    HISTORY_STORAGE_KEY,
    trimmed,
    compactStoredHistoryEntry,
    "history entries",
  );
  selectedHistoryId = savedHistory[0]?.id ?? null;
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
  // Drop selections whose entry no longer exists (deleted/cleared).
  for (const id of [...selectedShareIds]) {
    if (!history.some((entry) => entry.id === id)) {
      selectedShareIds.delete(id);
    }
  }
  updateShareSelectedButton();
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

  // Each row is a wrapper holding the share checkbox as a SIBLING of the clickable
  // button (a checkbox must never be nested inside a <button>).
  historyList.innerHTML = history
    .map(
      (entry) => `
        <div class="history-row">
          <input type="checkbox" class="history-select" data-history-id="${entry.id}" ${selectedShareIds.has(entry.id) ? "checked" : ""} aria-label="Vybrat ke sdílení" />
          <button class="history-item ${entry.id === selectedHistoryId ? "active" : ""}" type="button" data-history-id="${entry.id}">
            <strong>${escapeHtml(entry.question)}</strong>
            <span>${entry.mode === "retrieve" ? "Pouze zdroje" : "Odpověď"} · ${entry.sourceCount} zdrojů${entry.shared_id ? ` · <span class="history-shared-badge">Sdíleno ✓</span>` : ""}</span>
            <span>${formatHistoryTime(entry.createdAt)}</span>
          </button>
        </div>
      `,
    )
    .join("");

  for (const item of historyList.querySelectorAll(".history-item")) {
    item.addEventListener("click", () => {
      selectedHistoryId = Number(item.dataset.historyId);
      renderHistory();
    });
  }

  for (const checkbox of historyList.querySelectorAll(".history-select")) {
    checkbox.addEventListener("change", () => {
      const id = Number(checkbox.dataset.historyId);
      if (checkbox.checked) {
        selectedShareIds.add(id);
      } else {
        selectedShareIds.delete(id);
      }
      updateShareSelectedButton();
    });
  }

  const selectedEntry = history.find((entry) => entry.id === selectedHistoryId) || history[0];
  renderHistoryDetail(selectedEntry);
}

function updateShareSelectedButton() {
  if (!shareSelectedButton) {
    return;
  }
  const count = selectedShareIds.size;
  shareSelectedButton.textContent = `Sdílet vybrané (${count})`;
  shareSelectedButton.disabled = count === 0;
}

// --- Feature 3: shared history -------------------------------------------------

function getAuthorName() {
  try {
    return (localStorage.getItem(AUTHOR_NAME_STORAGE_KEY) || "").trim();
  } catch {
    return "";
  }
}

function setAuthorName(name) {
  const clean = String(name || "").trim();
  try {
    if (clean) {
      localStorage.setItem(AUTHOR_NAME_STORAGE_KEY, clean);
    } else {
      localStorage.removeItem(AUTHOR_NAME_STORAGE_KEY);
    }
  } catch {
    // localStorage may be unavailable; the name simply won't persist.
  }
  return clean;
}

// Returns the stored author name, prompting once (and persisting) when empty.
function ensureAuthorName() {
  let name = getAuthorName();
  if (!name) {
    const input = window.prompt("Pod jakým jménem chceš sdílet? (zobrazí se ostatním)", "");
    name = setAuthorName(input || "");
  }
  return name;
}

function renderAuthorName() {
  if (!historyAuthorNameLabel) {
    return;
  }
  const name = getAuthorName();
  historyAuthorNameLabel.textContent = name || "nastavit jméno";
}

function setHistoryShareStatus(message, variant = "") {
  if (!historyShareStatus) {
    return;
  }
  historyShareStatus.textContent = message || "";
  historyShareStatus.classList.toggle("success", variant === "success");
  historyShareStatus.classList.toggle("error", variant === "error");
}

// Persist a mutated field back onto a local history entry (note / shared marker)
// without re-rendering — callers decide when to refresh the view.
function mutateLocalHistoryEntry(id, mutate) {
  const history = getHistoryEntries();
  const entry = history.find((item) => item.id === id);
  if (!entry) {
    return;
  }
  mutate(entry);
  saveEntryListSafely(
    HISTORY_STORAGE_KEY,
    history,
    compactStoredHistoryEntry,
    "history entries",
  );
}

function updateLocalHistoryEntryNote(id, note) {
  mutateLocalHistoryEntry(id, (entry) => {
    entry.note = String(note || "");
  });
}

function updateLocalHistoryEntryShared(id, sharedId) {
  mutateLocalHistoryEntry(id, (entry) => {
    entry.shared_id = sharedId;
  });
}

// When a shared item is unshared, drop the "Sdíleno ✓" marker from any local
// entry that referenced it.
function clearLocalSharedMarker(sharedId) {
  const history = getHistoryEntries();
  let changed = false;
  for (const entry of history) {
    if (entry.shared_id === sharedId) {
      delete entry.shared_id;
      changed = true;
    }
  }
  if (changed) {
    saveEntryListSafely(
      HISTORY_STORAGE_KEY,
      history,
      compactStoredHistoryEntry,
      "history entries",
    );
  }
}

function setHistoryTab(tab) {
  activeHistoryTab = tab === "shared" ? "shared" : "mine";
  const mine = activeHistoryTab === "mine";
  historyTabMine.classList.toggle("active", mine);
  historyTabShared.classList.toggle("active", !mine);
  historyTabMine.setAttribute("aria-selected", mine ? "true" : "false");
  historyTabShared.setAttribute("aria-selected", mine ? "false" : "true");
  // Local-only affordances: multi-select share + per-item / clear deletion.
  shareSelectedButton.hidden = !mine;
  deleteHistoryItemButton.hidden = !mine;
  clearHistoryButton.hidden = !mine;
  setHistoryShareStatus("");
  if (mine) {
    renderHistory();
  } else {
    loadSharedHistory();
  }
}

async function fetchSharedHistory() {
  const response = await fetch("shared-history");
  if (!response.ok) {
    throw new Error("Nepodařilo se načíst sdílenou historii.");
  }
  const data = await safeJson(response);
  return Array.isArray(data) ? data : [];
}

// Fetches the server list into sharedHistoryItems. Only touches the dialog DOM
// while the Shared tab is active, so it can be called as a background refresh
// after a share/unshare done from the Moje historie tab.
async function loadSharedHistory() {
  const onSharedTab = activeHistoryTab === "shared";
  if (onSharedTab) {
    historyList.innerHTML = `<p class="history-empty">Načítám sdílené položky…</p>`;
  }
  try {
    sharedHistoryItems = await fetchSharedHistory();
  } catch (error) {
    sharedHistoryItems = [];
    if (activeHistoryTab === "shared") {
      historyList.innerHTML = `<p class="history-empty">${escapeHtml(error.message)}</p>`;
      historyDetail.innerHTML = `<p class="history-empty">Zkus to prosím načíst znovu.</p>`;
    }
    return;
  }
  if (activeHistoryTab === "shared") {
    renderSharedHistory();
  }
}

function renderSharedHistory() {
  if (!sharedHistoryItems.length) {
    historyList.innerHTML = `<p class="history-empty">Zatím nikdo nic nesdílel.</p>`;
    historyDetail.innerHTML = `<p class="history-empty">Zatím tu nejsou žádné sdílené položky.</p>`;
    return;
  }
  if (!sharedHistoryItems.some((item) => item.id === selectedSharedId)) {
    selectedSharedId = sharedHistoryItems[0].id;
  }
  historyList.innerHTML = sharedHistoryItems
    .map(
      (item) => `
        <div class="history-row">
          <button class="history-item ${item.id === selectedSharedId ? "active" : ""}" type="button" data-shared-id="${escapeHtml(item.id)}">
            <strong>${escapeHtml(item.question)}</strong>
            <span>${escapeHtml(item.author_name || "Anonym")} · ${item.mode === "retrieve" ? "Pouze zdroje" : "Odpověď"} · ${item.source_count} zdrojů</span>
            <span>${formatHistoryTime(item.shared_at)}</span>
          </button>
        </div>
      `,
    )
    .join("");

  for (const button of historyList.querySelectorAll(".history-item")) {
    button.addEventListener("click", () => {
      selectedSharedId = button.dataset.sharedId;
      renderSharedHistory();
    });
  }

  const selected = sharedHistoryItems.find((item) => item.id === selectedSharedId) || sharedHistoryItems[0];
  renderSharedHistoryDetail(selected);
}

// Owner (this browser) or an unlocked admin password may unshare an item.
function sharedItemManageable(item) {
  const owner = String(item.owner_id || "").trim();
  if (owner && owner === getBrowserOwnerId()) {
    return true;
  }
  return Boolean(llmUnlockPassword.value.trim());
}

function renderSharedHistoryDetail(item) {
  const canManage = sharedItemManageable(item);
  historyDetail.innerHTML = `
    <div class="history-detail-header">
      <div>
        <h3>${escapeHtml(item.question)}</h3>
        <p>${item.mode === "retrieve" ? "Pouze vyhledání zdrojů" : "Vygenerovaná odpověď"} · sdíleno ${formatHistoryTime(item.shared_at)}</p>
      </div>
      <div class="history-detail-actions">
        <button id="reuseSharedButton" type="button">Načíst do formuláře</button>
        ${canManage ? `<button id="unshareButton" type="button" class="history-unshare">Zrušit sdílení</button>` : ""}
      </div>
    </div>
    <section class="history-block history-shared-meta">
      <h4>Sdílel(a)</h4>
      <p class="history-shared-author">${escapeHtml(item.author_name || "Anonym")}</p>
      ${item.note ? `<p class="history-shared-note">${escapeHtml(item.note)}</p>` : ""}
    </section>
    <section class="history-block">
      <h4>Otázka</h4>
      <p class="history-question">${escapeHtml(item.question)}</p>
    </section>
    ${renderHistoryQueryTransform(item)}
    ${renderHistorySettingsAndAnswer(item)}
  `;

  historyDetail.querySelector("#reuseSharedButton")?.addEventListener("click", () => {
    // Shared items share the local entry shape, so the same restore path works.
    applyHistoryEntryToForm(item);
    historyDialog.close();
  });
  historyDetail.querySelector("#unshareButton")?.addEventListener("click", () => {
    unshareSharedItem(item);
  });

  mountHistoryDetailSources(item);
}

async function shareHistoryEntry(entry, authorName) {
  const payload = {
    owner_id: getBrowserOwnerId(),
    author_name: authorName,
    note: entry.note || "",
    question: entry.question || "",
    answer: entry.answer || "",
    mode: entry.mode || "",
    settings: entry.settings || {},
    sources: entry.sources || [],
    retrieved_chunks: entry.retrieved_chunks || [],
    source_count: entry.sourceCount || 0,
    created_at: entry.createdAt || "",
  };
  const response = await fetch("shared-history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await safeJson(response);
  if (!response.ok) {
    throw new Error(data.detail || "Sdílení položky selhalo.");
  }
  return data;
}

async function shareSelectedEntries() {
  if (!selectedShareIds.size) {
    return;
  }
  const authorName = ensureAuthorName();
  if (!authorName) {
    setHistoryShareStatus("Pro sdílení je potřeba zadat jméno.", "error");
    return;
  }
  renderAuthorName();
  const history = getHistoryEntries();
  const toShare = history.filter((entry) => selectedShareIds.has(entry.id));
  shareSelectedButton.disabled = true;
  setHistoryShareStatus(`Sdílím ${toShare.length}…`);
  let shared = 0;
  const failures = [];
  for (const entry of toShare) {
    try {
      const stored = await shareHistoryEntry(entry, authorName);
      updateLocalHistoryEntryShared(entry.id, stored.id);
      shared += 1;
    } catch (error) {
      failures.push(error.message);
    }
  }
  selectedShareIds.clear();
  if (failures.length) {
    setHistoryShareStatus(`Sdíleno ${shared}, selhalo ${failures.length}. ${failures[0]}`, shared ? "" : "error");
  } else {
    setHistoryShareStatus(`Sdíleno ${shared} ${shared === 1 ? "položka" : "položek"}. Díky!`, "success");
  }
  if (activeHistoryTab === "mine") {
    renderHistory();
  }
  // Refresh the server cache so the Shared tab is up to date next time it opens.
  await loadSharedHistory();
}

async function unshareSharedItem(item) {
  const params = new URLSearchParams({ owner_id: getBrowserOwnerId() });
  const adminPassword = llmUnlockPassword.value.trim();
  if (adminPassword) {
    params.set("admin_password", adminPassword);
  }
  setHistoryShareStatus("Ruším sdílení…");
  try {
    const response = await fetch(
      `shared-history/${encodeURIComponent(item.id)}?${params.toString()}`,
      { method: "DELETE" },
    );
    if (!response.ok && response.status !== 404) {
      const data = await safeJson(response);
      throw new Error(data.detail || "Zrušení sdílení selhalo.");
    }
    clearLocalSharedMarker(item.id);
    setHistoryShareStatus("Sdílení bylo zrušeno.", "success");
    await loadSharedHistory();
  } catch (error) {
    setHistoryShareStatus(error.message, "error");
  }
}

// The entry currently mounted in the history detail, for the copy buttons.
let historyDetailEntry = null;

function renderHistoryDetail(entry) {
  historyDetailEntry = entry;
  const sharedBadge = entry.shared_id
    ? ` <span class="history-shared-badge">Sdíleno ✓</span>`
    : "";
  historyDetail.innerHTML = `
    <div class="history-detail-header">
      <div>
        <h3>${escapeHtml(entry.question)}</h3>
        <p>${entry.mode === "retrieve" ? "Pouze vyhledání zdrojů" : "Vygenerovaná odpověď"} · ${formatHistoryTime(entry.createdAt)}${sharedBadge}</p>
      </div>
      <button id="reuseHistoryButton" type="button">Načíst do formuláře</button>
    </div>
    <section class="history-block">
      <h4>Otázka</h4>
      <p class="history-question">${escapeHtml(entry.question)}</p>
    </section>
    ${renderHistoryQueryTransform(entry)}
    <section class="history-block">
      <h4>Poznámka (uloží se při sdílení)</h4>
      <textarea id="historyNoteInput" class="history-note-input" rows="2" placeholder="Volitelná poznámka ke sdílení…">${escapeHtml(entry.note || "")}</textarea>
    </section>
    ${renderHistorySettingsAndAnswer(entry)}
  `;

  const reuseButton = historyDetail.querySelector("#reuseHistoryButton");
  reuseButton?.addEventListener("click", () => {
    applyHistoryEntryToForm(entry);
    historyDialog.close();
  });

  const noteInput = historyDetail.querySelector("#historyNoteInput");
  noteInput?.addEventListener("change", () => {
    // Keep the in-memory entry current for an immediate share, and persist. No
    // re-render here: it fires on blur and would eat a subsequent button click.
    entry.note = noteInput.value;
    updateLocalHistoryEntryNote(entry.id, noteInput.value);
  });

  mountHistoryDetailSources(entry);
}

function renderHistoryQueryTransform(entry) {
  const originalQuestion = String(entry.original_question || entry.question || "").trim();
  const retrievalQuery = String(entry.retrieval_query || entry.settings?.retrieval_query || "").trim();
  if (!retrievalQuery || retrievalQuery === originalQuestion) {
    return "";
  }
  const usedForAnswer = Boolean(
    entry.use_retrieval_query_for_answer ?? entry.settings?.use_retrieval_query_for_answer,
  );
  return `
    <section class="history-block">
      <h4>Upravený dotaz pro vyhledávání</h4>
      <p class="history-question">${escapeHtml(retrievalQuery)}</p>
      <p class="field-note">${
        usedForAnswer
          ? "Upravený dotaz byl použit také pro generování odpovědi."
          : "Pro generování odpovědi byl použit původní dotaz."
      }</p>
    </section>
  `;
}

// Shared between local (renderHistoryDetail) and server (renderSharedHistoryDetail)
// detail panes: the "Použitá nastavení" grid, the Feature-2 verbatim prompt
// toggle, the answer, and the sources placeholder (#historySources filled by
// mountHistoryDetailSources after innerHTML is set).
function renderHistorySettingsAndAnswer(entry) {
  const chunks = entry.retrieved_chunks || [];
  const sources = (entry.sources && entry.sources.length ? entry.sources : chunksToSources(chunks)) || [];
  return `
    <section class="history-block">
      <h4>Použitá nastavení</h4>
      <div class="settings-grid">
        ${renderSetting("WP", wpLabelFromSettings(entry.settings))}
        ${renderSetting("Prompt", promptPresetLabelFromSettings(entry.settings))}
        ${renderPromptNoteSetting(entry.settings)}
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
      ${renderVerbatimPromptDetails(entry.settings)}
    </section>
    ${
      entry.answer
        ? `<section class="history-block">
            <h4>Odpověď</h4>
            <div class="answer-actions">
              <button type="button" class="ghost-button" data-copy-scope="history">Kopírovat odpověď</button>
              <button type="button" class="ghost-button" data-copy-scope="history" data-copy-sources="1">Kopírovat se zdroji</button>
              <span class="copy-status" role="status" aria-live="polite"></span>
            </div>
            <div class="history-answer">${Avatar.renderMarkdown(entry.answer, sources, "history-source")}</div>
          </section>`
        : ""
    }
    <section class="history-block">
      <h4>Nalezené dokumenty</h4>
      <div id="historySources" class="sources history-sources"></div>
    </section>
  `;
}

function renderPromptNoteSetting(settings) {
  const note = promptPresetNoteFromSettings(settings);
  if (!note) {
    return "";
  }
  return `
    <div class="setting-card history-prompt-note">
      <span>Poznámka k promptu</span>
      <strong>${escapeHtml(note)}</strong>
    </div>
  `;
}

function promptPresetNoteFromSettings(settings) {
  if (Object.prototype.hasOwnProperty.call(settings || {}, "prompt_preset_note")) {
    return String(settings.prompt_preset_note || "").trim();
  }
  return promptPresetNote(getPromptPresetById(promptPresetIdFromSettings(settings)));
}

// Feature 2: collapsed-by-default verbatim system + user prompt. Both come from
// the entry's stored settings payload (system_prompt / user_prompt_template),
// which may be null when the prompt matched the built-in default.
function renderVerbatimPromptDetails(settings) {
  const systemPromptText = String(settings?.system_prompt || "").trim();
  const userPromptText = String(settings?.user_prompt_template || "").trim();
  const blocks = [];
  if (systemPromptText) {
    blocks.push(`<div class="history-verbatim-block"><h5>Systémový prompt</h5><pre>${escapeHtml(systemPromptText)}</pre></div>`);
  }
  if (userPromptText) {
    blocks.push(`<div class="history-verbatim-block"><h5>Šablona uživatelského promptu</h5><pre>${escapeHtml(userPromptText)}</pre></div>`);
  }
  const body = blocks.length
    ? blocks.join("")
    : `<p class="history-verbatim-empty">Přesné znění promptu nebylo uloženo.</p>`;
  return `
    <details class="history-verbatim">
      <summary>Zobrazit přesné znění promptu</summary>
      ${body}
    </details>
  `;
}

// Fills the #historySources placeholder produced by renderHistorySettingsAndAnswer.
// Budget fields are absent on shared items, so the notes simply render nothing.
function mountHistoryDetailSources(entry) {
  const chunks = entry.retrieved_chunks || [];
  const omittedChunks = entry.omitted_chunks || [];
  const sources = (entry.sources && entry.sources.length ? entry.sources : chunksToSources(chunks)) || [];
  const historySources = historyDetail.querySelector("#historySources");
  if (!historySources) {
    return;
  }
  const retrievalQuery = entry.retrieval_query || entry.settings?.retrieval_query || entry.question;
  // History replays a finished answer, so it opens directly in the settled
  // state: citation order, uncited collapsed, no streaming notice.
  const orderedCitationIds = Avatar.extractOrderedCitationIds(entry.answer || "");
  let historyView = Avatar.completedSourcesView(
    Avatar.createSourcesView({ canFlip: entry.mode !== "retrieve" }),
    orderedCitationIds,
  );
  const combined = withOmittedChunks(sources, chunks, omittedChunks);
  const renderHistorySources = () => {
    renderSourceCards(
      historySources,
      combined.sources,
      combined.chunks,
      retrievalQuery,
      Avatar.layoutSources(combined.sources, historyView, {
        orderedCitationIds,
        omittedCitationIds: combined.omittedCitationIds,
      }),
      "history-source",
      (patch) => {
        historyView = { ...historyView, ...patch };
        renderHistorySources();
      },
    );
  };
  renderHistorySources();
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
  // A history restore is another deliberate user choice; pending prepared-
  // question loads must not replace it even if the text happens to match an
  // earlier request snapshot.
  questionEditRevision += 1;
  managedQuestion = null;
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
  msearchCollection.value = entry.settings?.msearch_collection || msearchCollection.value;
  msearchMinConfidence.value = entry.settings?.msearch_min_confidence ?? msearchMinConfidence.value;
  msearchRescore.checked = Boolean(entry.settings?.msearch_rescore);
  topK.value = entry.settings?.top_k ?? topK.value;
  topKValue.value = topK.value;
  minRelativeScore.value = entry.settings?.min_relative_score ?? minRelativeScore.value;
  updateMsearchConfidenceLabel();
  updateThresholdLabels();
  updateRescoreThresholdNote();
  const restoredRetrievalQuery = String(
    entry.retrieval_query || entry.settings?.retrieval_query || "",
  ).trim();
  const restoredActionId = String(
    entry.query_transform_action_id || entry.settings?.query_transform_action_id || "",
  ).trim();
  // Force the inline rows to rebuild fresh for the restored question; the row
  // matching restoredActionId (if the action still exists) is re-populated
  // below, once renderQueryTransformSection() has rebuilt fresh row state.
  queryTransformSelectedActionId = null;
  queryTransformRowsQuestion = null;
  if (restoredRetrievalQuery && restoredRetrievalQuery !== question.value.trim()) {
    appliedQueryTransform = {
      originalQuestion: question.value,
      retrievalQuery: restoredRetrievalQuery,
      useForAnswer: Boolean(
        entry.use_retrieval_query_for_answer ?? entry.settings?.use_retrieval_query_for_answer,
      ),
      actionId: restoredActionId || null,
    };
  } else {
    appliedQueryTransform = null;
  }
  renderQueryTransformSection();
  if (appliedQueryTransform) {
    // A history item with an explicit retrieval query should restore that
    // query even when the profile's current automatic default is disabled.
    queryTransformApplyEnabled = true;
    renderQueryTransformSection();
  }
  // Older entries have no recorded action id, and a preset may have since
  // dropped/renamed the action that produced this result — in both cases
  // queryTransformRowState won't have a matching row, and we fall back to
  // just showing the applied-transform note above the (unselected) rows.
  if (appliedQueryTransform?.actionId && queryTransformRowState[appliedQueryTransform.actionId]) {
    applyQueryTransformRowResult(
      appliedQueryTransform.actionId,
      appliedQueryTransform.retrievalQuery,
      appliedQueryTransform.useForAnswer,
    );
    queryTransformSelectedActionId = appliedQueryTransform.actionId;
    updateQueryTransformRowSelectionUi();
    collapseOtherRows(appliedQueryTransform.actionId);
  }
  restoreAnswerFromHistoryEntry(entry);
  question.focus();
}

// Feature 1: render a stored entry's answer + sources back into the MAIN answer
// and source panels (the same ones live chat drives), so a past answer can be
// reviewed full-screen. Graceful for older / retrieve-only entries with missing
// fields. Works for both local entries and shared items (same shape).
function restoreAnswerFromHistoryEntry(entry) {
  const restoredChunks = entry.retrieved_chunks || [];
  const restoredSources = (entry.sources && entry.sources.length ? entry.sources : chunksToSources(restoredChunks)) || [];
  streamedAnswerText = entry.answer || "";
  currentAnswerSources = restoredSources;
  currentRetrievedChunks = restoredChunks;
  currentRetrievalQuery = entry.retrieval_query || entry.settings?.retrieval_query || entry.question || "";
  currentOmittedChunks = entry.omitted_chunks || [];
  currentBudgetWarnings = entry.chunk_budget_warnings || [];
  currentTokenBudget = entry.token_budget || null;
  currentConversationSummary = entry.conversation_summary || "";
  currentReasoning = entry.reasoning || "";
  renderReasoning(currentReasoning);
  // Stored entries have no baseline / rescore comparison to show.
  currentBaselineChunks = [];
  currentMsearchRescoreUsed = false;
  renderAnswer(streamedAnswerText);
  // A stored answer is final, so the panel opens in the settled state rather
  // than replaying the streaming notice.
  mainSourcesView = Avatar.createSourcesView({ canFlip: entry.mode !== "retrieve" });
  // renderSources internally re-applies renderBudgetNotes from the current* state
  // vars set above, mirroring the live flow.
  completeMainSources(currentAnswerSources, currentRetrievedChunks, streamedAnswerText);
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

loadSettings().catch((error) => {
  statusEl.className = "status error";
  statusEl.textContent = error.message;
});
