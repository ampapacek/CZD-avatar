export const CONVERSATION_SETTINGS_VERSION = 2;

export const CONVERSATION_RETRIEVAL_SETTING_KEYS = [
  "top_k",
  "msearch_rescore",
  "msearch_min_confidence",
  "min_relative_score",
];

const hasOwn = (object, key) => Object.prototype.hasOwnProperty.call(object || {}, key);

export function hasCurrentConversationSettings(settings) {
  return Number(settings?.settings_version) === CONVERSATION_SETTINGS_VERSION;
}

export function hasUsableConversationSettings(settings) {
  return Boolean(settings && typeof settings === "object" && !Array.isArray(settings));
}

// Settings version 2 added four retrieval controls. Older conversations keep
// every setting they already own and borrow only those missing values from the
// current main-page snapshot. This is an effective request/view object; callers
// must not persist it merely because the conversation was opened.
export function effectiveConversationSettings(settings, fallbackSettings) {
  if (!hasUsableConversationSettings(settings)) {
    return null;
  }
  const effective = { ...settings };
  for (const key of CONVERSATION_RETRIEVAL_SETTING_KEYS) {
    if (effective[key] === undefined && fallbackSettings?.[key] !== undefined) {
      effective[key] = fallbackSettings[key];
    }
  }
  return effective;
}

function sameSettingValue(left, right) {
  if (left === right) {
    return true;
  }
  if (left && right && typeof left === "object" && typeof right === "object") {
    return JSON.stringify(left) === JSON.stringify(right);
  }
  return false;
}

// A Settings-dialog edit is made while the live controls belong to a
// conversation. Patch only the values that changed during that dialog session
// into the saved main-page snapshot; unrelated conversation-owned values must
// not leak back to the main page.
export function mergeChangedSettings(target, before, after) {
  const merged = { ...(target || {}) };
  const previous = before || {};
  const current = after || {};
  for (const key of new Set([...Object.keys(previous), ...Object.keys(current)])) {
    if (!sameSettingValue(previous[key], current[key])) {
      if (hasOwn(current, key)) {
        merged[key] = current[key];
      } else {
        delete merged[key];
      }
    }
  }
  return merged;
}
