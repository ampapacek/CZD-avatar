// Which answer the conversation source panel is bound to.
//
// Every assistant turn renders its `[A1]`-style citations under one shared DOM
// scope, so a citation only resolves correctly while the panel carries the
// sources of the turn the reader is looking at. Binding the panel to the latest
// answer therefore makes `[A1]` in an early turn highlight the latest turn's A1
// — usually a different document, and worse the longer the thread runs.

const LATEST_HEADING = "Zdroje poslední odpovědi";

export function assistantMessageIndexes(messages) {
  const indexes = [];
  (messages || []).forEach((message, index) => {
    if (message?.role === "assistant") {
      indexes.push(index);
    }
  });
  return indexes;
}

// `null`, or an index that is no longer an assistant turn (a different thread,
// a deleted turn), means "follow the latest answer".
export function resolveSelectedAssistantIndex(messages, selectedIndex = null) {
  const indexes = assistantMessageIndexes(messages);
  if (!indexes.length) {
    return null;
  }
  return indexes.includes(selectedIndex) ? selectedIndex : indexes[indexes.length - 1];
}

export function conversationSourcesBinding(messages, selectedIndex = null) {
  const list = messages || [];
  const indexes = assistantMessageIndexes(list);
  const resolved = resolveSelectedAssistantIndex(list, selectedIndex);
  const message = resolved === null ? null : list[resolved];
  const isLatest = resolved === null || resolved === indexes[indexes.length - 1];
  const answerNumber = resolved === null ? 0 : indexes.indexOf(resolved) + 1;
  return {
    selectedIndex: resolved,
    message,
    isLatest,
    answerNumber,
    answerCount: indexes.length,
    heading: isLatest ? LATEST_HEADING : `Zdroje k ${answerNumber}. odpovědi`,
  };
}
