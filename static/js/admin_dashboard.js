// Admin dashboard: own Chart.js instances (so we control granularity, point
// labels and AJAX refresh) + the global period filter. Chart.js is bundled by
// Unfold and available as the global `Chart`.
(function () {
  "use strict";

  function cssColor(key, alpha) {
    var v = getComputedStyle(document.documentElement)
      .getPropertyValue("--color-" + key).trim();
    if (!v) v = "44 107 212";
    var triplet = v.split(/\s+/).join(",");
    return alpha != null ? "rgba(" + triplet + "," + alpha + ")" : "rgb(" + triplet + ")";
  }

  // Draws each point's value above it on line charts; thins labels when dense.
  var pointLabels = {
    id: "pointLabels",
    afterDatasetsDraw: function (chart) {
      if (!chart.$showLabels) return;
      var ctx = chart.ctx;
      chart.data.datasets.forEach(function (ds, di) {
        var meta = chart.getDatasetMeta(di);
        var n = meta.data.length;
        var step = n > 16 ? Math.ceil(n / 12) : 1;
        meta.data.forEach(function (pt, i) {
          if (i % step !== 0 && i !== n - 1) return;
          ctx.save();
          ctx.font = "600 11px Inter, sans-serif";
          ctx.fillStyle = cssColor("primary-600");
          ctx.textAlign = "center";
          ctx.fillText(String(ds.data[i]), pt.x, pt.y - 8);
          ctx.restore();
        });
      });
    },
  };

  function buildChart(canvas, cfg) {
    if (typeof Chart === "undefined") return null;
    var ctx = canvas.getContext("2d");
    if (cfg.type === "doughnut") {
      var ds = cfg.datasets[0] || { data: [], colors: [] };
      return new Chart(ctx, {
        type: "doughnut",
        data: {
          labels: cfg.labels,
          datasets: [{
            data: ds.data,
            backgroundColor: (ds.colors || []).map(function (k) { return cssColor(k); }),
            borderWidth: 0,
          }],
        },
        options: {
          responsive: true, maintainAspectRatio: false, cutout: "62%",
          plugins: { legend: { display: false } },
        },
      });
    }
    // line
    var lds = cfg.datasets[0] || { data: [], line: "primary-500", fill: "primary-100" };
    var chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: cfg.labels,
        datasets: [{
          label: lds.label || "",
          data: lds.data,
          borderColor: cssColor(lds.line || "primary-500"),
          backgroundColor: cssColor(lds.fill || "primary-100", 0.35),
          fill: true, tension: 0.4, pointRadius: 3, borderWidth: 2,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        layout: { padding: { top: 18 } },
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: cssColor("base-200", 0.6) } },
          x: { grid: { display: false } },
        },
      },
      plugins: [pointLabels],
    });
    chart.$showLabels = !!cfg.showLabels;
    return chart;
  }

  window.__dashCharts = window.__dashCharts || [];
  function destroyCharts() {
    window.__dashCharts.forEach(function (c) { try { c.destroy(); } catch (e) {} });
    window.__dashCharts = [];
  }
  function initCharts(root) {
    destroyCharts();
    (root || document).querySelectorAll("[data-dash-chart]").forEach(function (canvas) {
      var cfg;
      try { cfg = JSON.parse(canvas.getAttribute("data-chart")); } catch (e) { return; }
      var chart = buildChart(canvas, cfg);
      if (chart) window.__dashCharts.push(chart);
    });
  }

  function bindCopy(root) {
    (root || document).querySelectorAll("[data-copy-link]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var link = btn.getAttribute("data-copy-link");
        var label = btn.querySelector("[data-copy-label]");
        function flash() {
          if (!label) return;
          var prev = label.textContent;
          label.textContent = "✓";
          setTimeout(function () { label.textContent = prev; }, 1500);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(link).then(flash).catch(function () {});
        } else {
          var ta = document.createElement("textarea");
          ta.value = link; document.body.appendChild(ta); ta.select();
          try { document.execCommand("copy"); } catch (e) {}
          document.body.removeChild(ta); flash();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var tabsBox = document.querySelector("[data-dash-tabs]");
    var content = document.getElementById("dashboard-content");
    if (!tabsBox || !content) return;
    var url = tabsBox.getAttribute("data-dash-url");
    var ACTIVE = ["bg-primary-600", "text-white"];
    var INACTIVE = ["bg-base-100", "dark:bg-base-800", "text-font-subtle-light", "dark:text-font-subtle-dark"];
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".dash-tab"));

    function setActive(period) {
      tabs.forEach(function (t) {
        var on = t.getAttribute("data-period") === period;
        (on ? ACTIVE : INACTIVE).forEach(function (c) { t.classList.add(c); });
        (on ? INACTIVE : ACTIVE).forEach(function (c) { t.classList.remove(c); });
      });
    }

    function load(period) {
      setActive(period);
      content.style.opacity = "0.5";
      fetch(url + "?period=" + encodeURIComponent(period), {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      })
        .then(function (r) { return r.text(); })
        .then(function (html) {
          content.innerHTML = html;
          initCharts(content);
          bindCopy(content);
          try { sessionStorage.setItem("dash_period", period); } catch (e) {}
        })
        .catch(function () {})
        .finally(function () { content.style.opacity = ""; });
    }

    tabs.forEach(function (t) {
      t.addEventListener("click", function (e) {
        e.preventDefault();
        load(t.getAttribute("data-period"));
      });
    });

    // Initial: charts are already server-rendered for the active period. If a
    // different period was saved this session, switch to it.
    initCharts(content);
    bindCopy(content);
    var initial = tabsBox.getAttribute("data-active-period") || "month";
    var saved = null;
    try { saved = sessionStorage.getItem("dash_period"); } catch (e) {}
    if (saved && saved !== initial) load(saved);
  });
})();
