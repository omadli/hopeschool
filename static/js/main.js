// Hope School — frontend interactions
(function () {
  "use strict";
  var de = document.documentElement;

  // ---- scroll progress + sticky header ----
  var hdr = document.getElementById("hdr");
  var prog = document.getElementById("progress");
  function onScroll() {
    if (prog) {
      var p = de.scrollTop / (de.scrollHeight - de.clientHeight || 1);
      prog.style.transform = "scaleX(" + p + ")";
    }
    if (hdr) {
      if (window.scrollY > 10) {
        hdr.style.background = "var(--header)";
        hdr.style.backdropFilter = "blur(10px)";
        hdr.style.webkitBackdropFilter = "blur(10px)";
        hdr.style.borderBottomWidth = "1px";
        hdr.classList.add("bd");
        hdr.style.boxShadow = "0 2px 20px -14px rgba(0,0,0,.4)";
      } else {
        hdr.style.background = "transparent";
        hdr.style.backdropFilter = "none";
        hdr.style.borderBottomWidth = "0";
        hdr.style.boxShadow = "none";
      }
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  // Defer the first run a frame: calling it synchronously during load reads
  // layout (scrollTop/scrollHeight) and forces a reflow on the fresh DOM.
  requestAnimationFrame(onScroll);

  // ---- dark/light theme ----
  var themeBtn = document.getElementById("theme-btn");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      de.classList.toggle("dark");
      var dark = de.classList.contains("dark");
      try { localStorage.setItem("theme", dark ? "dark" : "light"); } catch (e) {}
      var m = document.getElementById("theme-color-meta");
      if (m) m.setAttribute("content", dark ? "#080d1a" : "#ffffff");
    });
  }

  // ---- language dropdown ----
  var lw = document.querySelector("[data-langwrap]");
  if (lw) {
    var lb = lw.querySelector("[data-langbtn]");
    var lm = lw.querySelector("[data-langmenu]");
    lb.addEventListener("click", function (e) { e.stopPropagation(); lm.classList.toggle("hidden"); });
    document.addEventListener("click", function () { lm.classList.add("hidden"); });
  }

  // ---- mobile drawer ----
  var burger = document.getElementById("burger");
  var drawer = document.getElementById("drawer");
  if (burger && drawer) {
    burger.addEventListener("click", function () { drawer.classList.toggle("hidden"); });
    drawer.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { drawer.classList.add("hidden"); });
    });
  }

  // ---- scroll reveal ----
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
  }, { threshold: 0.12 });
  document.querySelectorAll(".sr").forEach(function (el) { io.observe(el); });

  // ---- count up ----
  var cio = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      var el = e.target, to = +el.dataset.to || 0, c = 0, step = Math.max(1, Math.round(to / 45));
      (function t() { c += step; if (c >= to) { el.textContent = to; } else { el.textContent = c; requestAnimationFrame(t); } })();
      cio.unobserve(el);
    });
  }, { threshold: 0.6 });
  document.querySelectorAll(".count").forEach(function (c) { cio.observe(c); });

  // ---- carousels (autoplay + arrows) ----
  document.querySelectorAll("[data-carousel]").forEach(function (c) {
    var iv = +c.dataset.interval || 3500, t;
    function page() { return Math.max(c.clientWidth * 0.86, 180); }
    function next() {
      var max = c.scrollWidth - c.clientWidth - 6;
      if (c.scrollLeft >= max) c.scrollTo({ left: 0, behavior: "smooth" });
      else c.scrollBy({ left: page(), behavior: "smooth" });
    }
    function prev() { c.scrollBy({ left: -page(), behavior: "smooth" }); }
    function start() { t = setInterval(next, iv); }
    function stop() { clearInterval(t); }
    start();
    c.addEventListener("mouseenter", stop);
    c.addEventListener("mouseleave", start);
    c.addEventListener("touchstart", stop, { passive: true });
    c.addEventListener("touchend", function () { stop(); start(); }, { passive: true });
    var id = c.dataset.carousel;
    document.querySelectorAll('[data-next="' + id + '"]').forEach(function (b) { b.onclick = function () { stop(); next(); start(); }; });
    document.querySelectorAll('[data-prev="' + id + '"]').forEach(function (b) { b.onclick = function () { stop(); prev(); start(); }; });
  });

  // ---- announcement ticker ----
  var tk = document.getElementById("ticker");
  if (tk && window.__TICKER__ && window.__TICKER__.length) {
    var ti = 0;
    setInterval(function () {
      ti = (ti + 1) % window.__TICKER__.length;
      tk.classList.remove("ticker-item"); void tk.offsetWidth;
      tk.textContent = window.__TICKER__[ti];
      tk.classList.add("ticker-item");
    }, 4000);
  }

  // ---- map toggle (Google / Yandex) ----
  document.querySelectorAll("[data-map]").forEach(function (box) {
    var tabs = box.querySelectorAll("[data-map-tab]");
    tabs.forEach(function (t) {
      t.addEventListener("click", function () {
        var key = t.dataset.mapTab;
        box.querySelectorAll("[data-map-frame]").forEach(function (f) {
          f.classList.toggle("hidden", f.dataset.mapFrame !== key);
        });
        tabs.forEach(function (o) {
          var active = o === t;
          o.classList.toggle("bg-brand-blue-500", active);
          o.classList.toggle("text-white", active);
          o.classList.toggle("txt-soft", !active);
        });
      });
    });
  });

  // ---- modal ----
  var modal = document.getElementById("modal");
  function openM() { if (modal) { modal.classList.remove("hidden"); document.body.style.overflow = "hidden"; } }
  function closeM() { if (modal) { modal.classList.add("hidden"); document.body.style.overflow = ""; } }
  document.querySelectorAll("[data-open-modal]").forEach(function (b) { b.addEventListener("click", openM); });
  document.querySelectorAll("[data-close-modal]").forEach(function (b) { b.addEventListener("click", closeM); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeM(); });

  // ---- certificate lightbox (Sertifikatlar sahifasi) ----
  var certLb = document.getElementById("cert-lightbox");
  if (certLb) {
    var certImg = certLb.querySelector("[data-cert-image-el]");
    var certBadge = certLb.querySelector("[data-cert-badge-el]");
    var certDate = certLb.querySelector("[data-cert-date-el]");
    var certName = certLb.querySelector("[data-cert-name-el]");
    var certDesc = certLb.querySelector("[data-cert-description-el]");
    var certLink = certLb.querySelector("[data-cert-link-el]");

    function openCertLb(card) {
      var d = card.dataset;
      certImg.src = d.certImage || "";
      certImg.alt = d.certName || "";
      certBadge.textContent = d.certBadge || "";
      certBadge.classList.toggle("hidden", !d.certBadge);
      certDate.textContent = d.certDate || "";
      certDate.classList.toggle("hidden", !d.certDate);
      certName.textContent = d.certName || "";
      certDesc.textContent = d.certDescription || "";
      certDesc.classList.toggle("hidden", !d.certDescription);
      certLink.classList.toggle("hidden", !d.certLink);
      if (d.certLink) certLink.href = d.certLink;
      certLb.classList.remove("hidden");
      document.body.style.overflow = "hidden";
    }
    function closeCertLb() {
      certLb.classList.add("hidden");
      document.body.style.overflow = "";
    }
    document.querySelectorAll("[data-cert-open]").forEach(function (card) {
      card.addEventListener("click", function () { openCertLb(card); });
    });
    certLb.querySelectorAll("[data-cert-close]").forEach(function (b) {
      b.addEventListener("click", closeCertLb);
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeCertLb(); });
  }

  // ---- lead form submit (real endpoint, dependency-free) ----
  function showToast() {
    var t = document.getElementById("toast");
    if (t) { t.classList.remove("hidden"); setTimeout(function () { t.classList.add("hidden"); }, 3200); }
  }
  function setError(form, msg) {
    var box = form.querySelector("[data-form-error]");
    if (!box) return;
    if (msg) { box.textContent = msg; box.classList.remove("hidden"); }
    else { box.textContent = ""; box.classList.add("hidden"); }
  }
  function firstError(errors) {
    // errors: {field: [{message: "..."}, ...], ...} (Django get_json_data shape)
    try {
      for (var k in errors) {
        if (errors[k] && errors[k].length) return errors[k][0].message;
      }
    } catch (e) {}
    return null;
  }

  window.previewSubmit = function (e) {
    e.preventDefault();
    var form = e.target;
    var btn = form.querySelector('button[type="submit"]');
    var GENERIC = "Xatolik yuz berdi. Iltimos, qaytadan urinib koʻring.";
    setError(form, "");
    if (btn) btn.disabled = true;

    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        var d = res.data || {};
        if (d.ok) {
          form.reset();
          if (form.closest("#modal")) closeM();
          showToast();
        } else {
          setError(form, firstError(d.errors) || d.error || GENERIC);
        }
      })
      .catch(function () { setError(form, GENERIC); })
      .finally(function () { if (btn) btn.disabled = false; });

    return false;
  };

  // ---- capture ad source from the URL (hash or query) into lead forms ----
  // Links look like /uz/#contact?source=telegram — the source lives in the
  // hash fragment, which the server never sees. Read it here, remember it for
  // the session, and stamp it onto every hidden source input before submit.
  (function () {
    function fromParams(str) {
      try { return new URLSearchParams(str).get("source") || ""; }
      catch (e) { return ""; }
    }
    var hash = window.location.hash || "";
    var qIndex = hash.indexOf("?");
    // "#contact?source=telegram" is not a valid element id, so the browser
    // won't scroll to it. Scroll to the base anchor ("#contact") ourselves.
    if (qIndex > 1) {
      var anchor = document.getElementById(hash.slice(1, qIndex));
      if (anchor) { setTimeout(function () { anchor.scrollIntoView(); }, 0); }
    }
    var hashQuery = qIndex >= 0 ? hash.slice(qIndex + 1) : "";
    var src = fromParams(hashQuery) || fromParams(window.location.search);
    try {
      if (src) sessionStorage.setItem("lead_source", src);
      else src = sessionStorage.getItem("lead_source") || "";
    } catch (e) {}
    if (!src) return;
    document.querySelectorAll('input[name="source"]').forEach(function (i) {
      i.value = src;
    });
  })();

  // PWA install on the public site now relies on the browser's native install
  // UI (the linked web manifest) — no custom in-page prompt. The admin panel
  // keeps its own dedicated install button (see static/js/admin_pwa.js).

  // ---- only one <video> plays at a time (gallery grids show several) ----
  // "play" doesn't bubble, so listen on the capture phase at document level —
  // this also covers videos added to the DOM later, with one listener.
  document.addEventListener("play", function (e) {
    if (e.target.tagName !== "VIDEO") return;
    document.querySelectorAll("video").forEach(function (v) {
      if (v !== e.target) v.pause();
    });
  }, true);
})();
