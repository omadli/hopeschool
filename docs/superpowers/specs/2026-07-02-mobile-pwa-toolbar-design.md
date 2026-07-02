# Design — Mobile polish, PWA install, and browser-toolbar theming

Date: 2026-07-02
Status: Approved

## Goal

Make the public site feel native on mobile and installable as an app, and make
the Unfold admin more comfortable on phones. Three user requests:

1. Admin panel more mobile-friendly.
2. Home page mobile design: fix the browser **toolbar / theme colors** on mobile.
3. Add a **web manifest + install icon** so the site can be installed on mobile.
4. (Added mid-session) robots.txt.

## Current state (verified)

- `templates/base.html` head has `viewport-fit=cover`, a favicon fallback chain,
  and a pre-paint theme script (`base.html:24`) that adds `.dark` to `<html>`
  from `localStorage.theme`. **No `theme-color` and no manifest exist.**
- Dark mode is driven by a `.dark` class (localStorage), **not** the OS
  `prefers-color-scheme` — the sun/moon toggle lives in `static/js/main.js:38`.
- Background tokens (`assets/css/source.css`): light `--bg: #ffffff`, dark
  `--bg: #080d1a`.
- Brand: blue `#2c6bd4`, red `#da2128`, white surfaces. Logo
  `static/img/logo.png` is 240×160, transparent — **not square** (needs icon gen).
- Admin: django-unfold with prior mobile work — sidebar toggle
  (`static/js/admin_sidebar.js`), responsive tweaks in
  `static/css/admin_extra.css`. Loaded via `UNFOLD["STYLES"]`/`["SCRIPTS"]`.
- `robots.txt` **already exists** — dynamic view `apps/common/views.py`
  `robots_txt`, routed in `config/urls.py`, emits an absolute `Sitemap:` line.
- Admin path is obfuscated: `ADMIN_URL` (env) `= /kirma-bu-yerga/`.

## Workstreams

### 1. Browser toolbar color (`theme-color`) — adaptive

Add an adaptive `theme-color`: light `#ffffff`, dark `#080d1a` (matches `--bg`).
Because dark mode is a class (not OS pref), a static `<meta media>` alone will
not follow the manual toggle. Wire it in the two places that already own theme
state:

- `base.html:24` pre-paint inline script sets the meta `content` up-front → no
  flash on load.
- `main.js:38` toggle handler updates the meta on sun/moon click.

Also add iOS PWA head meta: `apple-mobile-web-app-capable`,
`mobile-web-app-capable`, `apple-mobile-web-app-status-bar-style` (`default`),
`apple-mobile-web-app-title` (`Hope School`), and `apple-touch-icon`.

### 2. Web manifest + icons

- `static/site.webmanifest` (static, cache-friendly): `name "Hope School"`,
  `short_name "Hope"`, `start_url "/"`, `scope "/"`, `display "standalone"`,
  `theme_color`/`background_color` `#ffffff`, `lang "uz"`, icons array.
- Generate square icons from `logo.png` with Pillow, committed under
  `static/img/pwa/`:
  - `icon-192.png`, `icon-512.png` — logo centered on white.
  - `icon-512-maskable.png` — logo centered with ~20% safe-zone padding, white
    bg (`purpose: "maskable"`).
  - `apple-touch-icon.png` 180×180, white bg (iOS blackens transparency).
- Link `<link rel="manifest" href="{% static 'site.webmanifest' %}">` +
  apple-touch-icon in `base.html` head.

### 3. Custom "Install app" button

Scope = **installable + visible install button** (no offline service worker —
avoids cache-invalidation risk against WhiteNoise's hashed assets; a marketing
site does not need offline).

- New `static/js/pwa.js` (or fold into `main.js`): capture
  `beforeinstallprompt` (preventDefault, stash the event), reveal a dismissible
  **"Ilovani o'rnatish"** chip; on tap call `.prompt()`; hide when the choice is
  made, on `appinstalled`, or when `display-mode: standalone`.
- iOS fires no event → no intrusive UI (optional future "Share → Add to Home
  Screen" hint).
- Placement: a small dismissible chip; exact spot (header menu vs. above the
  bottom mobile bar) finalized during implementation against a real viewport.

### 4. Admin mobile polish (general pass)

Light-touch additions to `static/css/admin_extra.css`, scoped to `@media`
(max-width) so they do not fight Unfold's Tailwind:

- Larger tap targets on result rows, buttons, links.
- Changelist tables: reliable horizontal scroll on narrow screens.
- **Sticky submit / "Saqlash" bar** so save is always reachable on long forms.
- Inputs ≥16px font (prevents iOS auto-zoom) + comfortable height.
- Filter sidebar and the language-switcher row wrap cleanly.

PWA stays **public-only** — admin is behind login, not made installable.

### 5. robots.txt

Already works. One fix: its `Disallow: /admin/` predates the obfuscated
`ADMIN_URL`. We deliberately do **not** publish the secret admin path (that would
defeat the obfuscation), so keep `Disallow: /admin/` (blocks default guesses)
and add `Disallow: /ariza/` (POST-only lead endpoint). No other change.

## Testing / verification

- Load home on a mobile viewport (Chrome DevTools) → confirm toolbar color in
  light and dark, and after toggling theme.
- Lighthouse / installability check passes (manifest + icons + start_url).
- Admin on a narrow viewport → save bar reachable, tables scroll, no zoom on
  focus.
- Full test suite stays green (261 tests). Add a test asserting the new
  `robots.txt` line if the view changes.

## Out of scope

- Offline service worker / caching.
- Making the admin installable.
- Redesigning the bottom mobile action bar (call + apply) — only additive.
