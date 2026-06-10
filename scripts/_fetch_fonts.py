"""One-off: download self-hosted woff2 for Manrope/Onest and generate the
inline _fonts.html partial. Run once, then delete. Not part of the app."""
import os
import re
import urllib.request

FAMILIES = "Manrope:wght@700;800&family=Onest:wght@400;500;600;700"
CSS_URL = f"https://fonts.googleapis.com/css2?family={FAMILIES}&display=swap"
# uz/en need latin (incl. U+02BB ʻ, which is in the 'latin' subset); ru needs cyrillic.
KEEP_SUBSETS = {"latin", "latin-ext", "cyrillic"}
# Modern Chrome UA so Google returns woff2 (not ttf).
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

FONTS_DIR = os.path.join("assets", "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read() if binary else r.read().decode("utf-8")


css = fetch(CSS_URL)
# Each @font-face is preceded by a /* subset */ comment.
blocks = re.findall(r"/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})", css, re.S)
print(f"Found {len(blocks)} @font-face blocks in css2")

faces = []  # (family, weight, subset, local_filename, unicode_range)
for subset, block in blocks:
    if subset not in KEEP_SUBSETS:
        continue
    fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
    weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
    src = re.search(r"src:\s*url\(([^)]+)\)", block).group(1)
    urange = re.search(r"unicode-range:\s*([^;]+);", block).group(1).strip()
    fname = f"{fam.lower()}-{weight}-{subset}.woff2"
    dest = os.path.join(FONTS_DIR, fname)
    if not os.path.exists(dest):
        with open(dest, "wb") as f:
            f.write(fetch(src, binary=True))
    faces.append((fam, weight, subset, fname, urange))
    print(f"  {fname:32s} {os.path.getsize(dest)//1024} KB")

# --- Generate the partial -------------------------------------------------
# Critical above-the-fold latin fonts to preload (uz/en default): H1 (Manrope
# 800) and body (Onest 400). Other weights/subsets load on demand via swap.
PRELOAD = [("manrope", "800", "latin"), ("onest", "400", "latin")]

lines = ["{% load static %}",
         "{# Self-hosted fonts (Manrope display + Onest body). Inlined @font-face",
         "   avoids a render-blocking external Google Fonts CSS request. #}"]
for fam, w, sub in PRELOAD:
    href = "{%% static 'fonts/%s-%s-%s.woff2' %%}" % (fam, w, sub)
    lines.append(f'<link rel="preload" as="font" type="font/woff2" '
                 f'href="{href}" crossorigin>')
lines.append("<style>")
for fam, weight, subset, fname, urange in faces:
    href = "{%% static 'fonts/%s' %%}" % fname
    lines.append(
        "@font-face{font-family:'%s';font-style:normal;font-weight:%s;"
        "font-display:swap;src:url(\"%s\") format('woff2');unicode-range:%s;}"
        % (fam, weight, href, urange))
lines.append("</style>")

with open(os.path.join("templates", "partials", "_fonts.html"), "w",
          encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines) + "\n")
print(f"\nWrote templates/partials/_fonts.html ({len(faces)} @font-face)")
