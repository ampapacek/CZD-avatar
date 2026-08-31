export const CONVERSATION_SETTINGS_VERSION = 2;

const hasOwn = (object, key) => Object.prototype.hasOwnProperty.call(object || {}, key);

export function hasCurrentConversationSettings(settings) {
  return Number(settings?.settings_version) === CONVERSATION_SETTINGS_VERSION;
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
