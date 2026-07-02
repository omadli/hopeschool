/* Admin camera QR scanner.
 *
 * Attaches a "scan QR" button to any input carrying data-qr-scan (the
 * Certificate.external_url field). Scanning a CEFR certificate's QR code fills
 * the field with the verification URL; saving then auto-imports the PDF.
 *
 * Requires HTTPS (or localhost) for getUserMedia — the browser blocks the
 * camera on plain http. Decoding uses the vendored jsQR (global `jsQR`).
 */
(function () {
  "use strict";

  function setup(input) {
    if (input.dataset.qrReady) return;
    input.dataset.qrReady = "1";

    // Localized strings come from the widget's data-* attrs (active admin
    // language); fall back to Uzbek if the attribute is absent.
    var d = input.dataset;
    var T = {
      label: d.qrLabel || "📷 QR kodni skanerlash",
      close: d.qrClose || "Yopish",
      found: d.qrFound || "Topildi:",
      opening: d.qrOpening || "Kamera ochilmoqda…",
      aim: d.qrAim || "QR kodni kameraga toʻgʻrilang…",
      denied: d.qrDenied || "Kameraga ruxsat berilmadi:",
      nocam: d.qrNocam || "Bu brauzerda kamera ishlamaydi. Havolani qoʻlda kiriting.",
    };

    var wrap = document.createElement("div");
    wrap.style.marginTop = "6px";

    var btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = T.label;
    btn.style.cssText =
      "padding:6px 12px;border-radius:8px;border:1px solid #ccc;" +
      "cursor:pointer;background:#f5f5f5;font-size:13px;";

    var box = document.createElement("div");
    box.style.cssText = "display:none;margin-top:8px;max-width:340px;";

    var video = document.createElement("video");
    video.setAttribute("playsinline", "");
    video.style.cssText = "width:100%;border-radius:10px;background:#000;";

    var status = document.createElement("p");
    status.style.cssText = "font-size:12px;color:#666;margin:6px 0;";

    var stop = document.createElement("button");
    stop.type = "button";
    stop.textContent = T.close;
    stop.style.cssText =
      "padding:4px 10px;border-radius:8px;border:1px solid #ccc;cursor:pointer;font-size:12px;";

    box.appendChild(video);
    box.appendChild(status);
    box.appendChild(stop);
    wrap.appendChild(btn);
    wrap.appendChild(box);
    input.parentNode.appendChild(wrap);

    var stream = null;
    var raf = null;
    var canvas = document.createElement("canvas");

    function cleanup() {
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      if (stream) {
        stream.getTracks().forEach(function (t) { t.stop(); });
      }
      stream = null;
    }

    function scan() {
      if (!stream) return;
      if (video.readyState === video.HAVE_ENOUGH_DATA && window.jsQR) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        var img = ctx.getImageData(0, 0, canvas.width, canvas.height);
        var code = window.jsQR(img.data, img.width, img.height, {
          inversionAttempts: "dontInvert",
        });
        if (code && code.data) {
          input.value = code.data.trim();
          input.dispatchEvent(new Event("change", { bubbles: true }));
          status.textContent = T.found + " " + code.data;
          cleanup();
          return;
        }
      }
      raf = requestAnimationFrame(scan);
    }

    btn.addEventListener("click", function () {
      box.style.display = "block";
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        status.textContent = T.nocam;
        return;
      }
      status.textContent = T.opening;
      navigator.mediaDevices
        .getUserMedia({ video: { facingMode: "environment" } })
        .then(function (s) {
          stream = s;
          video.srcObject = s;
          video.play();
          status.textContent = T.aim;
          raf = requestAnimationFrame(scan);
        })
        .catch(function (e) {
          status.textContent = T.denied + " " + e.message;
        });
    });

    stop.addEventListener("click", function () {
      cleanup();
      box.style.display = "none";
    });
  }

  function init() {
    document.querySelectorAll("[data-qr-scan]").forEach(setup);
  }

  if (document.readyState !== "loading") {
    init();
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
