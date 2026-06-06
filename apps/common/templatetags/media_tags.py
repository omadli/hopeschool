"""Responsive image helpers (Core Web Vitals).

Renders a ``<picture>`` with a WebP ``<source>`` (one or two widths) plus an
``<img>`` fallback in the original format. Thumbnails are produced with
easy-thumbnails so every variant ships explicit ``width``/``height`` (no CLS),
``loading``/``decoding`` hints and a ``class`` hook for the existing card CSS.

Usage in templates::

    {% load media_tags %}
    {% if course.image %}
      {% responsive_img course.image alt=course.name css="h-full w-full object-cover" width=900 %}
    {% endif %}

The caller keeps its own ``{% if image %}`` guard so the gradient/placeholder
fallback is preserved when no image is uploaded.
"""
from __future__ import annotations

from django import template
from easy_thumbnails.exceptions import InvalidImageFormatError
from easy_thumbnails.files import get_thumbnailer

register = template.Library()


def _thumb(image, width, fmt=None):
    """Return a ThumbnailFile for ``image`` at ``width`` px (height auto).

    When ``fmt`` is given (e.g. "WEBP"), the generated file is both encoded *and*
    named with that extension — easy-thumbnails' PRESERVE_EXTENSIONS otherwise
    keeps the source extension (.jpg) even for WebP-encoded bytes, which mislabels
    the file and breaks the ``<source type="image/webp">`` contract.

    Returns ``None`` if the source is missing/unreadable so the caller can fall
    back to its placeholder instead of crashing.
    """
    options = {"size": (width, 0), "crop": False, "upscale": False, "quality": 82}
    try:
        thumbnailer = get_thumbnailer(image)
        if fmt:
            options["format"] = fmt
            # Force the output extension (and disable source-extension
            # preservation) so the variant is e.g. ...format-WEBP.webp.
            thumbnailer.thumbnail_extension = fmt.lower()
            thumbnailer.thumbnail_preserve_extensions = False
        return thumbnailer.get_thumbnail(options)
    except (InvalidImageFormatError, OSError, ValueError, KeyError):
        return None


@register.inclusion_tag("partials/_img.html")
def responsive_img(image, alt="", css="", width=900, width_2x=None,
                   eager=False, fetchpriority=None, sizes=None):
    """Build context for ``partials/_img.html``.

    Args:
        image: an ImageFieldFile (the caller guards truthiness).
        alt: alt text.
        css: CSS classes applied to the inner ``<img>``.
        width: primary rendered width in px (drives the 1x variant).
        width_2x: optional second (retina) width; adds a ``2x`` srcset entry.
        eager: above-the-fold images load eagerly (no lazy-load).
        fetchpriority: e.g. "high" for the LCP/hero image.
        sizes: optional ``sizes`` attribute for the responsive sources.
    """
    width = int(width)
    base = _thumb(image, width)
    webp = _thumb(image, width, fmt="WEBP")
    base2 = webp2 = None
    if width_2x:
        width_2x = int(width_2x)
        base2 = _thumb(image, width_2x)
        webp2 = _thumb(image, width_2x, fmt="WEBP")

    webp_srcset = img_srcset = ""
    img_src = ""
    out_w = out_h = None

    if base:
        img_src = base.url
        out_w, out_h = base.width, base.height

    # Descriptor choice:
    #  * with ``sizes`` (variable-width layout images): use width (``w``)
    #    descriptors keyed on the *actual* generated width so the browser honours
    #    ``sizes`` and selects by layout-width × DPR. Actual widths also
    #    auto-correct the upscale=False cap (an 800px source requested at 900 is
    #    labelled 800w, and a duplicate-width 2x variant is dropped).
    #  * without ``sizes`` (fixed-size images like avatars): use density
    #    (``1x``/``2x``) descriptors so the browser picks purely on DPR.
    def _srcset(t1, t2):
        if not t1:
            return ""
        if sizes:
            parts = [f"{t1.url} {t1.width}w"]
            if t2 and t2.width > t1.width:
                parts.append(f"{t2.url} {t2.width}w")
            return ", ".join(parts)
        parts = [f"{t1.url} 1x"]
        if t2 and t2.width > t1.width:
            parts.append(f"{t2.url} 2x")
        return ", ".join(parts)

    img_srcset = _srcset(base, base2)
    webp_srcset = _srcset(webp, webp2)

    return {
        "img_src": img_src,
        "img_srcset": img_srcset,
        "webp_srcset": webp_srcset,
        "alt": alt,
        "css": css,
        "width": out_w,
        "height": out_h,
        "loading": "eager" if eager else "lazy",
        "fetchpriority": fetchpriority,
        "sizes": sizes,
    }
