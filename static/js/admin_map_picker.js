// Admin location picker (Leaflet + OpenStreetMap, no API key)
(function () {
  "use strict";

  function init() {
    var mapEl = document.getElementById("hs-map");
    if (!mapEl || typeof L === "undefined") return;
    if (mapEl.dataset.ready) return;
    mapEl.dataset.ready = "1";

    var latInput = document.getElementById("id_latitude");
    var lngInput = document.getElementById("id_longitude");
    if (!latInput || !lngInput) return;

    var lat = parseFloat(latInput.value) || 41.311081;   // Tashkent default
    var lng = parseFloat(lngInput.value) || 69.240562;
    var hasValue = latInput.value && lngInput.value;

    var map = L.map("hs-map").setView([lat, lng], hasValue ? 16 : 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap",
    }).addTo(map);

    // Point Leaflet at the self-hosted marker images. The widget passes the
    // resolved (hash-aware) static URLs via data-* so icons work under
    // WhiteNoise's manifest storage in production, not just in dev.
    if (mapEl.dataset.icon) {
      L.Icon.Default.mergeOptions({
        iconUrl: mapEl.dataset.icon,
        iconRetinaUrl: mapEl.dataset.icon2x || mapEl.dataset.icon,
        shadowUrl: mapEl.dataset.shadow || "",
      });
    }

    var marker = L.marker([lat, lng], { draggable: true }).addTo(map);

    function set(ll) {
      latInput.value = ll.lat.toFixed(6);
      lngInput.value = ll.lng.toFixed(6);
    }
    if (!hasValue) set(marker.getLatLng());

    map.on("click", function (e) { marker.setLatLng(e.latlng); set(e.latlng); });
    marker.on("dragend", function () { set(marker.getLatLng()); });

    var btn = document.getElementById("hs-map-search-btn");
    var inp = document.getElementById("hs-map-search-input");
    function search() {
      var q = (inp.value || "").trim();
      if (!q) return;
      btn.disabled = true;
      fetch("https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + encodeURIComponent(q),
            { headers: { "Accept-Language": "uz,ru,en" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          btn.disabled = false;
          if (d && d[0]) {
            var la = parseFloat(d[0].lat), lo = parseFloat(d[0].lon);
            map.setView([la, lo], 16);
            marker.setLatLng([la, lo]);
            set({ lat: la, lng: lo });
          } else {
            alert("Manzil topilmadi.");
          }
        })
        .catch(function () { btn.disabled = false; });
    }
    btn.addEventListener("click", search);
    inp.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); search(); }
    });

    setTimeout(function () { map.invalidateSize(); }, 300);
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
