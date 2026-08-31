export function sourcePanelPresentation(sourceCount, collapsed = false) {
  const count = Math.max(0, Number.isFinite(Number(sourceCount)) ? Number(sourceCount) : 0);
  const hasSources = count > 0;
  const isCollapsed = hasSources && Boolean(collapsed);
  return {
    count,
    hasSources,
    isCollapsed,
    panelHidden: !hasSources,
    bodyHidden: !hasSources || isCollapsed,
    reopenHidden: !isCollapsed,
    label: `Zdroje (${count})`,
  };
}

export function nextTabIndex(currentIndex, key, tabCount) {
  if (!tabCount) {
    return -1;
  }
  if (key === "Home") {
    return 0;
  }
  if (key === "End") {
    return tabCount - 1;
  }
  if (key === "ArrowRight" || key === "ArrowDown") {
    return (currentIndex + 1) % tabCount;
  }
  if (key === "ArrowLeft" || key === "ArrowUp") {
    return (currentIndex - 1 + tabCount) % tabCount;
  }
  return currentIndex;
}

export function wpTopicLabel(label) {
  const cleaned = String(label || "")
    .replace(/^\s*WP\s*\d+\s*(?:[–—-]\s*)?/iu, "")
    .trim();
  return cleaned || "vybranému v nabídce";
}
