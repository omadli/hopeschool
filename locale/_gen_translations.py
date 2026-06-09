# -*- coding: utf-8 -*-
"""One-off helper: draft RU/EN (project) + UZ/RU (Unfold) translations via the
deep-translator engine, batched. Output is reviewed by hand and pasted into
_build_catalogs.py / _build_uz_admin.py. Not imported anywhere at runtime.
"""
import os
import sys

import django

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "locale"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.common.translation import _translate_segments  # noqa: E402

import _build_catalogs as bc  # noqa: E402

# --- Project strings still missing a RU translation (UZ source) ---
missing = sorted({s for s in bc.singular if bc.norm(s) not in bc.RU})

# --- Unfold UI strings (EN source) the user wants in uz/ru ---
UNFOLD = [
    "Add row", "All applications", "Apply Filters", "Cancel", "Change",
    "Change password", "Clear", "Clear all filters", "Click to cancel",
    "Click to download", "Close", "Dark", "Delete", "Expand row", "False",
    "Filters", "General", "Go back", "Hide counts", "Light", "Log in again",
    "Log out", "More actions", "Navigate", "Next", "No data", "No results found",
    "Nothing matched your search", "Previous", "Recent searches",
    "Record picture", "Remove", "Reset filters", "Run", "Run the selected action",
    "Save", "Save and add another", "Save and continue editing", "Save and view",
    "Save as new", "Select", "Select all rows", "Show counts", "Submit", "System",
    "This item will be deleted.",
    "This page yielded into no results. Create a new item or reset your filters.",
    "Toggle password visibility", "True", "Type to search", "Unknown", "View",
    "View site", "Search apps and models...",
]


def emit(title, keys, ru, en=None):
    print(f"\n# ===== {title} =====")
    for i, k in enumerate(keys):
        line = f"    {k!r}: {ru[i]!r},"
        if en is not None:
            line += f"   # en: {en[i]!r}"
        print(line)


pr_ru = _translate_segments(missing, "ru", "uz")
pr_en = _translate_segments(missing, "en", "uz")
emit("PROJECT -> RU (paste into RU map)", missing, pr_ru)
emit("PROJECT -> EN (paste into EN map)", missing, pr_en)

uf_uz = _translate_segments(UNFOLD, "uz", "en")
uf_ru = _translate_segments(UNFOLD, "ru", "en")
emit("UNFOLD -> UZ (paste into _build_uz_admin UNFOLD)", UNFOLD, uf_uz)
emit("UNFOLD -> RU (paste into _build_catalogs UNFOLD_RU)", UNFOLD, uf_ru)
