from django import forms
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class LeafletLocationWidget(forms.TextInput):
    """Renders an interactive Leaflet map + address search above the latitude
    input. Clicking/dragging the marker (or searching) fills #id_latitude and
    #id_longitude automatically. No API key required (OpenStreetMap).

    Leaflet is self-hosted under static/vendor/leaflet/ (no third-party CDN in
    the authenticated admin, and no SRI to maintain); the marker image URLs are
    resolved with static() so they stay correct under manifest hashing."""

    class Media:
        css = {"all": (
            "vendor/leaflet/leaflet.css",
            "css/admin_map_picker.css",
        )}
        js = (
            "vendor/leaflet/leaflet.js",
            "js/admin_map_picker.js",
        )

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        search_ph = _("Manzilni qidiring (masalan: Chilonzor, Toshkent)…")
        find_label = _("Qidirish")
        hint = _("Xaritani bosing yoki belgini suring — koordinatalar avtomatik to‘ladi.")
        icon = static("vendor/leaflet/images/marker-icon.png")
        icon_2x = static("vendor/leaflet/images/marker-icon-2x.png")
        shadow = static("vendor/leaflet/images/marker-shadow.png")
        map_html = f"""
        <div class="hs-map-picker">
          <div class="hs-map-search">
            <input type="text" id="hs-map-search-input" placeholder="{search_ph}" autocomplete="off">
            <button type="button" id="hs-map-search-btn">{find_label}</button>
          </div>
          <div id="hs-map" data-icon="{icon}" data-icon-2x="{icon_2x}" data-shadow="{shadow}"></div>
          <p class="hs-map-hint">{hint}</p>
        </div>
        """
        return mark_safe(map_html + input_html)
