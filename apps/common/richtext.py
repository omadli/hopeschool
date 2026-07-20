"""Server-side sanitizer for admin-authored CKEditor rich text.

CKEditor HTML is only as trustworthy as the staff account that wrote it — a
compromised or rogue editor could otherwise store ``<script>``/``onerror=``
that runs for every public visitor (stored XSS). Public templates render these
fields through :func:`sanitize_rich_html` so only safe markup survives, mirroring
``apps.siteconfig.models.sanitize_map_embed`` but for the full rich-text tag set
plus video-embed iframes restricted to known hosts.
"""
from urllib.parse import urlparse

import nh3

# Hosts allowed as <iframe> embeds (CKEditor mediaEmbed: video + maps).
_IFRAME_HOSTS = (
    "youtube.com", "youtube-nocookie.com", "player.vimeo.com", "vimeo.com",
    "google.com", "yandex.uz", "yandex.ru", "yandex.com",
)

# nh3's default allowlist (Mozilla's) already drops scripts, event handlers and
# non-http(s) URLs; we only add <iframe> (for embeds) on top of it.
_TAGS = nh3.ALLOWED_TAGS | {"iframe"}
_ATTRS = {
    **nh3.ALLOWED_ATTRIBUTES,
    "iframe": {"src", "width", "height", "allow", "allowfullscreen",
               "frameborder", "loading", "referrerpolicy", "title", "style"},
    "img": {"src", "alt", "width", "height", "style", "class"},
}


def _host_ok(host):
    host = (host or "").lower()
    return any(host == h or host.endswith("." + h) for h in _IFRAME_HOSTS)


def _attr_filter(tag, attr, value):
    # Strip iframe src unless it points at an allowed embed host (an src-less
    # iframe renders nothing — harmless — so the whole node needn't be removed).
    if tag == "iframe" and attr == "src" and not _host_ok(urlparse(value).hostname):
        return None
    return value


def sanitize_rich_html(html):
    """Return XSS-safe HTML (str) from admin CKEditor input, or ''."""
    if not html or not html.strip():
        return ""
    return nh3.clean(
        html,
        tags=_TAGS,
        attributes=_ATTRS,
        url_schemes={"http", "https", "mailto", "tel"},
        attribute_filter=_attr_filter,
        link_rel="nofollow noopener noreferrer",
    )
