// On a narrow screen the sources sit below the answer, so following a citation
// scrolls the reader away from the sentence they were reading. A floating
// button takes them back: it appears once the cited marker has left the
// screen, and goes away when it is used, when the reader scrolls back to the
// marker on their own, or when the marker is re-rendered or hidden.

export function isInViewport(element, viewportHeight) {
  const rect = element.getBoundingClientRect();
  return rect.bottom > 0 && rect.top < viewportHeight;
}

// `button` is the floating button; `viewportHeight` reads the current height,
// so a phone's toolbar collapsing mid-scroll is taken into account.
export function createCitationReturn({ button, viewportHeight }) {
  let marker = null;
  let leftView = false;

  function disarm() {
    marker = null;
    leftView = false;
    button.hidden = true;
  }

  // A marker inside a dialog needs the button in that dialog: a modal dialog
  // sits above everything else on the page, the button included.
  function hostFor(element) {
    return element.closest("dialog") || element.ownerDocument.body;
  }

  function markerGone() {
    if (!marker.isConnected || !marker.getClientRects().length) {
      return true;
    }
    const dialog = marker.closest("dialog");
    return Boolean(dialog && !dialog.open);
  }

  function update() {
    if (!marker) {
      return;
    }
    if (markerGone()) {
      disarm();
      return;
    }
    if (isInViewport(marker, viewportHeight())) {
      if (leftView) {
        disarm();
      }
      return;
    }
    leftView = true;
    button.hidden = false;
  }

  function arm(next) {
    marker = next;
    leftView = false;
    button.hidden = true;
    const host = hostFor(next);
    if (button.parentElement !== host) {
      host.append(button);
    }
    update();
  }

  function returnToMarker() {
    const target = marker;
    disarm();
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return {
    arm,
    disarm,
    update,
    returnToMarker,
    get marker() {
      return marker;
    },
  };
}
