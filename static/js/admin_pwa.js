/*
 * Admin PWA install button.
 *
 * Chromium fires `beforeinstallprompt` when the admin manifest makes the panel
 * installable. We stash that event and reveal the header "Install app" button;
 * clicking it triggers the native prompt. The button stays hidden when the app
 * is already installed / running standalone, or on browsers that never fire the
 * event (Firefox, iOS Safari — those users install via the browser menu).
 */
(function () {
  "use strict";

  var btn = document.getElementById("admin-pwa-install");
  if (!btn) return;

  var deferredPrompt = null;

  function isStandalone() {
    return (
      (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) ||
      window.navigator.standalone === true
    );
  }

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (!isStandalone()) btn.classList.remove("hidden");
  });

  btn.addEventListener("click", function () {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(function () {
      deferredPrompt = null;
      btn.classList.add("hidden");
    });
  });

  window.addEventListener("appinstalled", function () {
    btn.classList.add("hidden");
  });
})();
