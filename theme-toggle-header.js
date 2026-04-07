/**
 * Palm theme mounts the light/dark control inside #sidebar-content, which is
 * `display: none` below the lg breakpoint — the toggle never paints on mobile.
 * Move the control to document.body and pin it to the header top-right.
 *
 * When the Mintlify AI assistant panel is open its close button occupies the
 * same top-right corner, so we hide the toggle while the chat is open.
 */
(function () {
  var SELECTOR = 'button[aria-label="Toggle dark mode"]';
  var debounceTimer;

  // Selectors that indicate the Mintlify AI chat panel is open.
  // We watch for any of these appearing in the DOM.
  var CHAT_SELECTORS = [
    '[data-chat]',
    '[aria-label="Close chat"]',
    '[aria-label="Close AI assistant"]',
    '[aria-label="Close assistant"]',
    '[data-testid="chat-window"]',
    '[data-testid="chat-panel"]',
    '.chat-panel',
    '#chat-panel',
    '[class*="chatPanel"]',
    '[class*="ChatPanel"]',
    '[class*="aiChat"]',
    '[class*="AiChat"]',
    '[class*="chatWindow"]',
    '[class*="ChatWindow"]',
  ];

  function isChatOpen() {
    return CHAT_SELECTORS.some(function (sel) {
      try {
        var el = document.querySelector(sel);
        if (!el) return false;
        var style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden';
      } catch (e) {
        return false;
      }
    });
  }

  function rightInset() {
    return window.matchMedia('(min-width: 1024px)').matches
      ? 'max(3rem, env(safe-area-inset-right, 0px))'
      : 'max(1rem, env(safe-area-inset-right, 0px))';
  }

  function applyStyles(btn) {
    btn.style.setProperty('position', 'fixed', 'important');
    btn.style.setProperty(
      'top',
      'calc(env(safe-area-inset-top, 0px) + 1.125rem)',
      'important'
    );
    btn.style.setProperty('right', rightInset(), 'important');
    btn.style.setProperty('z-index', '99999', 'important');
  }

  function syncVisibility() {
    var btn = document.querySelector(SELECTOR);
    if (!btn) return;
    if (isChatOpen()) {
      btn.style.setProperty('display', 'none', 'important');
    } else {
      btn.style.removeProperty('display');
    }
  }

  function pin() {
    var nodes = document.querySelectorAll(SELECTOR);
    if (!nodes.length) return;

    var btn = nodes[0];
    for (var i = 1; i < nodes.length; i++) {
      nodes[i].remove();
    }

    if (btn.parentNode !== document.body) {
      document.body.appendChild(btn);
    }
    applyStyles(btn);
    syncVisibility();
  }

  function schedulePin() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(pin, 50);
  }

  function scheduleSync() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(syncVisibility, 50);
  }

  function init() {
    pin();
    setTimeout(pin, 0);
    setTimeout(pin, 150);
    setTimeout(pin, 500);
    setTimeout(pin, 1500);

    var n = 0;
    var intervalId = setInterval(function () {
      pin();
      if (++n >= 30) clearInterval(intervalId);
    }, 200);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.addEventListener('resize', function () {
    var btn = document.querySelector(SELECTOR);
    if (btn) applyStyles(btn);
  });

  window.addEventListener('popstate', schedulePin);

  function startObserver() {
    var obs = new MutationObserver(scheduleSync);
    obs.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class', 'hidden'] });
  }

  function startSidebarObserver() {
    var root = document.getElementById('sidebar-content') || document.body;
    var obs = new MutationObserver(schedulePin);
    obs.observe(root, { childList: true, subtree: true });
  }

  if (document.body) {
    startObserver();
    startSidebarObserver();
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      startObserver();
      startSidebarObserver();
    });
  }
})();
