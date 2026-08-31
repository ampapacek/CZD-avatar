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

export function conversationTurnRailItems(messages) {
  const list = messages || [];
  return assistantMessageIndexes(list)
    .filter((assistantIndex) => {
      const answer = list[assistantIndex];
      return Boolean(String(answer?.content || "").trim() || String(answer?.reasoning || "").trim());
    })
    .map((assistantIndex, index) => {
      let userIndex = assistantIndex - 1;
      while (userIndex >= 0 && list[userIndex]?.role !== "user") {
        userIndex -= 1;
      }
      const answer = list[assistantIndex];
      const question = String(answer?.question || list[userIndex]?.content || "").trim();
      return {
        answerNumber: index + 1,
        assistantIndex,
        userIndex: userIndex >= 0 ? userIndex : assistantIndex,
        question,
      };
    });
}

export function conversationTurnRailSignature(conversationId, messages) {
  return JSON.stringify([
    conversationId,
    ...conversationTurnRailItems(messages).map((item) => [
      item.assistantIndex,
      item.userIndex,
      item.question,
    ]),
  ]);
}

export function conversationTurnTarget(dataset) {
  const assistantIndex = Number(dataset?.conversationAssistantIndex);
  const userIndex = Number(dataset?.conversationUserIndex);
  if (!Number.isInteger(assistantIndex)) {
    return null;
  }
  return {
    assistantIndex,
    scrollIndex: Number.isInteger(userIndex) ? userIndex : assistantIndex,
  };
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
