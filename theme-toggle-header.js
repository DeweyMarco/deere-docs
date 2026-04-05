/**
 * Palm theme mounts the light/dark control inside #sidebar-content, which is
 * `display: none` below the lg breakpoint — the toggle never paints on mobile.
 * Move the control to document.body and pin it to the header top-right.
 */
(function () {
  var SELECTOR = 'button[aria-label="Toggle dark mode"]';
  var debounceTimer;

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
  }

  function schedulePin() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(pin, 50);
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
    var root = document.getElementById('sidebar-content') || document.body;
    var obs = new MutationObserver(schedulePin);
    obs.observe(root, { childList: true, subtree: true });
  }

  if (document.body) startObserver();
  else document.addEventListener('DOMContentLoaded', startObserver);
})();
