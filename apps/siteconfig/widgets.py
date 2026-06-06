from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class LeafletLocationWidget(forms.TextInput):
    """Renders an interactive Leaflet map + address search above the latitude
    input. Clicking/dragging the marker (or searching) fills #id_latitude and
    #id_longitude automatically. No API key required (OpenStreetMap)."""

    class Media:
        css = {"all": (
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
            "css/admin_map_picker.css",
        )}
        js = (
            "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
            "js/admin_map_picker.js",
        )

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        search_ph = _("Manzilni qidiring (masalan: Chilonzor, Toshkent)…")
        find_label = _("Qidirish")
        hint = _("Xaritani bosing yoki belgini suring — koordinatalar avtomatik to‘ladi.")
        map_html = f"""
        <div class="hs-map-picker">
          <div class="hs-map-search">
            <input type="text" id="hs-map-search-input" placeholder="{search_ph}" autocomplete="off">
            <button type="button" id="hs-map-search-btn">{find_label}</button>
          </div>
          <div id="hs-map"></div>
          <p class="hs-map-hint">{hint}</p>
        </div>
        """
        return mark_safe(map_html + input_html)
