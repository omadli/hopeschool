# CRM — Ariza Manbasi (Lead Source) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Track which ad channel each application (lead) comes from via a hidden `source` field, and surface per-channel lead stats + copy-able ad links in the admin CRM.

**Architecture:** A new `LeadSource` model (channel with slug/icon/image) drives a hidden `source` field on the public form. JS reads the slug from the URL hash/query and fills the field; the view resolves it to a `LeadSource` FK server-side (unknown → `site`). The admin gets a `Manbalar` CRUD list under a `CRM` sidebar group plus a per-source stats block (period switch + count-up + copy-link) on the existing dashboard. The old free-text `source` becomes `referrer`.

**Tech Stack:** Django 5, django-unfold admin, modeltranslation (not used here), Tailwind (Unfold build), vanilla JS. Tests: Django `TestCase`.

## Global Constraints

- **Django comments:** NEVER use multi-line `{# … #}` — it leaks as page text. Use single-line `{# … #}` or `{% comment %}…{% endcomment %}`. (CLAUDE.md)
- **Dev server port:** `python manage.py runserver 8001` (not 8000).
- **Source name is single (not translatable)** — no modeltranslation registration for `LeadSource`.
- **Built-in channels:** slugs `site`, `telegram`, `instagram`, `facebook`; all `is_protected=True` (cannot be deleted or re-slugged in admin).
- **Default source slug:** `site` (`LeadSource.DEFAULT_SLUG`).
- **Image field** uses `apps.common.validators.image_validators`, `upload_to="crm/sources/"`.
- **Test command:** `python manage.py test apps.leads apps.analytics` (run from repo root, venv active).
- Run all commands from repo root `D:\Projects\hopeschool`.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `apps/leads/models.py` | `LeadSource` model + helpers; `Lead.referrer`/`Lead.source` FK | Modify |
| `apps/leads/migrations/0003_leadsource.py` | Create `LeadSource` (auto-generated) | Create |
| `apps/leads/migrations/0004_lead_source_referrer.py` | Rename `source`→`referrer`, add `source` FK (hand-written) | Create |
| `apps/leads/migrations/0005_seed_lead_sources.py` | Seed 4 built-ins + backfill existing leads (data) | Create |
| `apps/leads/views.py` | Resolve POSTed `source` slug → FK; capture referrer | Modify |
| `templates/sections/_contact.html` | Hidden `source` input | Modify |
| `templates/partials/_modal.html` | Hidden `source` input | Modify |
| `static/js/main.js` | Read `source` from hash/query → fill inputs | Modify |
| `apps/leads/admin.py` | `LeadSourceAdmin`; update `LeadAdmin` (`referrer`, `source`) | Modify |
| `config/settings.py` | `CRM` sidebar group | Modify |
| `apps/analytics/dashboard.py` | `source_stats` + `source_period` context | Modify |
| `templates/admin/index.html` | CRM stats block + count-up/copy JS | Modify |
| `apps/leads/notifications.py` | `🔗 Manba:` line in Telegram message | Modify |
| `apps/leads/tests.py` | Model/view/admin/notification tests | Modify |
| `apps/analytics/tests.py` | dashboard `source_stats` tests | Modify |

---

## Task 1: `LeadSource` model + `Lead` refactor + migrations

**Files:**
- Modify: `apps/leads/models.py`
- Create: `apps/leads/migrations/0003_leadsource.py` (auto), `apps/leads/migrations/0004_lead_source_referrer.py` (hand), `apps/leads/migrations/0005_seed_lead_sources.py` (hand)
- Test: `apps/leads/tests.py`

**Interfaces:**
- Produces:
  - `LeadSource` model with fields `name, slug, icon, image, color, is_protected` (+ `order, is_active, created_at, updated_at` from `OrderedActiveModel`).
  - `LeadSource.DEFAULT_SLUG = "site"`
  - `LeadSource.get_default() -> LeadSource`
  - `LeadSource.resolve(slug: str | None) -> LeadSource` (active match or default)
  - `LeadSource.brand_key -> str` (property; social_icon key or `""`)
  - `LeadSource.build_link(domain: str, lang: str) -> str`
  - `Lead.referrer` (CharField, was `source`); `Lead.source` (FK → `LeadSource`, `SET_NULL`, `related_name="leads"`)

- [ ] **Step 1: Write the failing tests**

Add these imports/tests to `apps/leads/tests.py`. Add `LeadSource` to the existing models import line (`from apps.leads.models import Lead, LeadSource`), and append this class after `LeadModelTests`:

```python
class LeadSourceModelTests(TestCase):
    """LeadSource resolve/default/build_link + built-ins from migration."""

    def test_builtins_created_by_migration(self):
        self.assertEqual(
            LeadSource.objects.filter(is_protected=True).count(), 4
        )
        self.assertTrue(
            LeadSource.objects.filter(slug="site", is_protected=True).exists()
        )

    def test_resolve_known_active_slug(self):
        self.assertEqual(LeadSource.resolve("telegram").slug, "telegram")

    def test_resolve_unknown_slug_returns_site(self):
        self.assertEqual(LeadSource.resolve("bogus").slug, "site")

    def test_resolve_empty_returns_site(self):
        self.assertEqual(LeadSource.resolve("").slug, "site")
        self.assertEqual(LeadSource.resolve(None).slug, "site")

    def test_resolve_inactive_slug_returns_site(self):
        LeadSource.objects.filter(slug="telegram").update(is_active=False)
        self.assertEqual(LeadSource.resolve("telegram").slug, "site")

    def test_brand_key_maps_site_to_website(self):
        self.assertEqual(LeadSource.objects.get(slug="site").brand_key, "website")
        self.assertEqual(
            LeadSource.objects.get(slug="telegram").brand_key, "telegram"
        )

    def test_build_link_uses_lang_and_slug(self):
        src = LeadSource.resolve("instagram")
        self.assertEqual(
            src.build_link("hopeschool.uz", "ru"),
            "https://hopeschool.uz/ru/#contact?source=instagram",
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.leads.tests.LeadSourceModelTests -v 2`
Expected: FAIL/ERROR — `ImportError: cannot import name 'LeadSource'`.

- [ ] **Step 3: Add the `LeadSource` model (no `Lead` changes yet)**

In `apps/leads/models.py`, update the imports and add the model. New imports at top:

```python
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import OrderedActiveModel, TimeStampedModel
from apps.common.utils import normalize_phone
from apps.common.validators import image_validators
```

Add this class **above** `Lead`:

```python
# Slugs that render as an existing brand icon (see social_icon template tag).
# 'site' shows the generic website glyph.
_BRAND_SLUGS = {
    "site": "website", "telegram": "telegram", "instagram": "instagram",
    "facebook": "facebook", "youtube": "youtube", "tiktok": "tiktok",
    "twitter": "twitter", "linkedin": "linkedin", "whatsapp": "whatsapp",
}


class LeadSource(OrderedActiveModel):
    """An ad channel a lead can arrive from (site, telegram, instagram, …).

    Drives the hidden ``source`` field on the public form and the CRM stats
    block. Built-in channels are ``is_protected`` so they cannot be deleted or
    re-slugged — their slugs are baked into shared ad links."""

    DEFAULT_SLUG = "site"

    name = models.CharField(_("Nomi"), max_length=80)
    slug = models.SlugField(_("Slug"), max_length=80, unique=True)
    icon = models.CharField(
        _("Ikonka"), max_length=48, blank=True,
        help_text=_("Material Symbols nomi (masalan: public). Rasm boʻlmaganda ishlatiladi."),
    )
    image = models.ImageField(
        _("Rasm (hisobot uchun)"), upload_to="crm/sources/", blank=True,
        validators=image_validators,
    )
    color = models.CharField(
        _("Rang"), max_length=7, blank=True,
        help_text=_("#RRGGBB. Boʻsh boʻlsa asosiy rang ishlatiladi."),
    )
    is_protected = models.BooleanField(_("Himoyalangan"), default=False, editable=False)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Manba")
        verbose_name_plural = _("Manbalar")

    def __str__(self):
        return self.name

    @property
    def brand_key(self):
        """social_icon platform key for this slug, or '' if not a known brand."""
        return _BRAND_SLUGS.get(self.slug, "")

    def build_link(self, domain, lang):
        """Absolute application link in ``lang`` carrying this source slug."""
        domain = (domain or "").strip().rstrip("/")
        return f"https://{domain}/{lang}/#contact?source={self.slug}"

    @classmethod
    def get_default(cls):
        """The 'site' channel; created on the fly if it was ever removed."""
        obj, _created = cls.objects.get_or_create(
            slug=cls.DEFAULT_SLUG,
            defaults={"name": "Sayt", "icon": "public", "is_protected": True},
        )
        return obj

    @classmethod
    def resolve(cls, slug):
        """Active source matching ``slug``; the default 'site' source otherwise."""
        if slug:
            match = cls.objects.filter(slug=slug, is_active=True).first()
            if match:
                return match
        return cls.get_default()
```

- [ ] **Step 4: Generate the `LeadSource` migration**

Run: `python manage.py makemigrations leads`
Expected: creates `apps/leads/migrations/0003_leadsource.py` (a single `CreateModel`). Note the exact filename — if it is not `0003_leadsource.py`, use its real name as the dependency in Step 6.

- [ ] **Step 5: Add the `Lead` field changes to the model**

In `apps/leads/models.py`, inside `class Lead`, **replace** the existing `source` field:

```python
    source = models.CharField(
        _("Manba"), max_length=255, blank=True,
        help_text=_("UTM yoki referrer (avtomatik toʻldiriladi)."),
    )
```

with these two fields:

```python
    referrer = models.CharField(
        _("Referrer"), max_length=255, blank=True,
        help_text=_("UTM yoki referrer (avtomatik toʻldiriladi)."),
    )
    source = models.ForeignKey(
        "leads.LeadSource", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="leads", verbose_name=_("Manba"),
    )
```

- [ ] **Step 6: Hand-write the rename + FK migration**

Do NOT run `makemigrations` for this — the autodetector would misread `source` (CharField→FK) as an `AlterField` and drop the referrer data. Create `apps/leads/migrations/0004_lead_source_referrer.py` by hand:

```python
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0003_leadsource"),
    ]

    operations = [
        migrations.RenameField(
            model_name="lead",
            old_name="source",
            new_name="referrer",
        ),
        migrations.AlterField(
            model_name="lead",
            name="referrer",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="Referrer",
                help_text="UTM yoki referrer (avtomatik toʻldiriladi).",
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="source",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="leads",
                to="leads.leadsource",
                verbose_name="Manba",
            ),
        ),
    ]
```

- [ ] **Step 7: Write the data migration (seed built-ins + backfill)**

Create `apps/leads/migrations/0005_seed_lead_sources.py`:

```python
from django.db import migrations

BUILTINS = [
    {"slug": "site", "name": "Sayt", "icon": "public", "order": 0},
    {"slug": "telegram", "name": "Telegram", "icon": "send", "order": 1},
    {"slug": "instagram", "name": "Instagram", "icon": "photo_camera", "order": 2},
    {"slug": "facebook", "name": "Facebook", "icon": "thumb_up", "order": 3},
]


def seed_sources(apps, schema_editor):
    LeadSource = apps.get_model("leads", "LeadSource")
    Lead = apps.get_model("leads", "Lead")
    site = None
    for row in BUILTINS:
        obj, _created = LeadSource.objects.get_or_create(
            slug=row["slug"],
            defaults={
                "name": row["name"], "icon": row["icon"],
                "order": row["order"], "is_protected": True,
            },
        )
        if row["slug"] == "site":
            site = obj
    # Existing leads all came through the website form.
    Lead.objects.filter(source__isnull=True).update(source=site)


def unseed_sources(apps, schema_editor):
    LeadSource = apps.get_model("leads", "LeadSource")
    LeadSource.objects.filter(
        slug__in=[b["slug"] for b in BUILTINS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0004_lead_source_referrer"),
    ]

    operations = [
        migrations.RunPython(seed_sources, unseed_sources),
    ]
```

- [ ] **Step 8: Apply migrations**

Run: `python manage.py migrate leads`
Expected: `0003`, `0004`, `0005` all apply with `OK`.

- [ ] **Step 9: Run tests to verify they pass**

Run: `python manage.py test apps.leads.tests.LeadSourceModelTests -v 2`
Expected: PASS (7 tests). If `test_builtins_created_by_migration` fails, confirm `0005` ran and `BUILTINS` slugs match.

- [ ] **Step 10: Commit**

```bash
git add apps/leads/models.py apps/leads/migrations/0003_leadsource.py apps/leads/migrations/0004_lead_source_referrer.py apps/leads/migrations/0005_seed_lead_sources.py apps/leads/tests.py
git commit -m "feat(crm): LeadSource model + Lead source/referrer refactor"
```

---

## Task 2: View resolves `source` slug → FK; captures referrer

**Files:**
- Modify: `apps/leads/views.py`
- Modify: `templates/sections/_contact.html`, `templates/partials/_modal.html`
- Test: `apps/leads/tests.py`

**Interfaces:**
- Consumes: `LeadSource.resolve` (Task 1), `Lead.referrer`, `Lead.source` (Task 1).
- Produces: `POST /ariza/` reads `source` (slug string) and `utm_source`/referer; sets `lead.source` (FK) and `lead.referrer`.

- [ ] **Step 1: Write the failing tests**

In `apps/leads/tests.py`, inside `class LeadCreateViewTests`, **replace** `test_utm_source_captured` with the referrer version and add three source tests:

```python
    # --- UTM/referrer captured on `referrer` ---
    def test_utm_source_captured_as_referrer(self):
        data = {**self._valid_data, "utm_source": "google"}
        self._post(data=data)
        lead = Lead.objects.get()
        self.assertEqual(lead.referrer, "google")

    # --- source slug resolves to the LeadSource FK ---
    def test_source_slug_resolved_to_fk(self):
        data = {**self._valid_data, "source": "telegram"}
        self._post(data=data)
        self.assertEqual(Lead.objects.get().source.slug, "telegram")

    def test_unknown_source_defaults_to_site(self):
        data = {**self._valid_data, "source": "bogus-xyz"}
        self._post(data=data)
        self.assertEqual(Lead.objects.get().source.slug, "site")

    def test_missing_source_defaults_to_site(self):
        self._post()
        self.assertEqual(Lead.objects.get().source.slug, "site")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.leads.tests.LeadCreateViewTests -v 2`
Expected: FAIL — `AttributeError: 'Lead' object has no attribute 'referrer'` and/or `source` is a string, not a FK.

- [ ] **Step 3: Update the view**

In `apps/leads/views.py`:

Add the import near the top (with the other imports):

```python
from .models import LeadSource
```

**Rename** `_capture_source` to `_capture_referrer` (body unchanged):

```python
def _capture_referrer(request):
    """Derive a referrer string from utm params or the HTTP referer."""
    utm = request.POST.get("utm_source") or request.GET.get("utm_source")
    if utm:
        return utm[:255]
    referer = request.META.get("HTTP_REFERER", "")
    return referer[:255]
```

In `lead_create`, **replace**:

```python
    lead = form.save(commit=False)
    lead.source = _capture_source(request)
    lead.save()
```

with:

```python
    lead = form.save(commit=False)
    lead.referrer = _capture_referrer(request)
    lead.source = LeadSource.resolve(request.POST.get("source"))
    lead.save()
```

- [ ] **Step 4: Add the hidden `source` input to both forms**

In `templates/sections/_contact.html`, directly after the honeypot line (the `name="website"` input, line ~18), add:

```html
          <input type="hidden" name="source" value="site">
```

In `templates/partials/_modal.html`, directly after its honeypot line (the `name="website"` input, line ~14), add:

```html
        <input type="hidden" name="source" value="site">
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.leads.tests.LeadCreateViewTests -v 2`
Expected: PASS (all view tests, including the 4 new/updated ones).

- [ ] **Step 6: Commit**

```bash
git add apps/leads/views.py templates/sections/_contact.html templates/partials/_modal.html apps/leads/tests.py
git commit -m "feat(crm): resolve source slug to FK, capture referrer separately"
```

---

## Task 3: Front-end — read `source` from URL into the form (client JS)

**Files:**
- Modify: `static/js/main.js`

**Interfaces:**
- Consumes: hidden `input[name="source"]` from Task 2.
- Produces: on load, fills every `input[name="source"]` from `location.hash`/`location.search` `?source=…`, persisted in `sessionStorage["lead_source"]`.

> Pure client-side; no pytest coverage. Verified manually in Step 3.

- [ ] **Step 1: Add the source-capture snippet**

In `static/js/main.js`, inside the top-level IIFE, immediately **before** the closing PWA comment block / `})();` at the end (after the `window.previewSubmit = …` assignment, ~line 193), insert:

```javascript
  // ---- capture ad source from the URL (hash or query) into lead forms ----
  // Links look like /uz/#contact?source=telegram — the source lives in the
  // hash fragment, which the server never sees. Read it here, remember it for
  // the session, and stamp it onto every hidden source input before submit.
  (function () {
    function fromParams(str) {
      try { return new URLSearchParams(str).get("source") || ""; }
      catch (e) { return ""; }
    }
    var hash = window.location.hash || "";
    var hashQuery = hash.indexOf("?") >= 0 ? hash.slice(hash.indexOf("?") + 1) : "";
    var src = fromParams(hashQuery) || fromParams(window.location.search);
    try {
      if (src) sessionStorage.setItem("lead_source", src);
      else src = sessionStorage.getItem("lead_source") || "";
    } catch (e) {}
    if (!src) return;
    document.querySelectorAll('input[name="source"]').forEach(function (i) {
      i.value = src;
    });
  })();
```

- [ ] **Step 2: Rebuild static (collectstatic not needed in dev; runserver serves `static/`)**

No build step for plain JS. If the project serves via `collectstatic` locally, run `python manage.py collectstatic --noinput`; otherwise skip.

- [ ] **Step 3: Manual verification**

Run: `python manage.py runserver 8001`
Open `http://localhost:8001/uz/#contact?source=telegram`, open DevTools console, run:
```js
document.querySelector('input[name="source"]').value
```
Expected: `"telegram"`. Navigate to `/uz/` (no hash) in the same tab → value stays `"telegram"` (sessionStorage). Fresh tab on `/uz/` → value is `"site"`.

- [ ] **Step 4: Commit**

```bash
git add static/js/main.js
git commit -m "feat(crm): fill hidden source field from URL hash/query"
```

---

## Task 4: `LeadSource` admin + `CRM` sidebar group

**Files:**
- Modify: `apps/leads/admin.py`
- Modify: `config/settings.py`
- Test: `apps/leads/tests.py`

**Interfaces:**
- Consumes: `LeadSource`, `Lead.referrer`, `Lead.source` (Task 1).
- Produces: `admin:leads_leadsource_changelist`; `LeadSourceAdmin.has_delete_permission(request, obj)` returns `False` for protected sources.

- [ ] **Step 1: Write the failing tests**

In `apps/leads/tests.py`, add this class (near `LeadAdminTests`). It needs `RequestFactory` (already imported) and `LeadSourceAdmin`:

```python
@override_settings(STORAGES=_STATIC_STORAGE)
class LeadSourceAdminTests(TestCase):
    """CRM sources changelist + protection of built-ins."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_src", password="pass12345",
            email="admin_src@test.com",
        )
        self.client.force_login(self.superuser)

    def test_leadsource_changelist_returns_200(self):
        url = reverse("admin:leads_leadsource_changelist")
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_protected_source_cannot_be_deleted(self):
        from django.contrib.admin.sites import AdminSite
        from apps.leads.admin import LeadSourceAdmin
        from apps.leads.models import LeadSource
        admin_obj = LeadSourceAdmin(LeadSource, AdminSite())
        request = RequestFactory().get("/")
        request.user = self.superuser
        site = LeadSource.objects.get(slug="site")
        self.assertFalse(admin_obj.has_delete_permission(request, site))

    def test_custom_source_can_be_deleted(self):
        from django.contrib.admin.sites import AdminSite
        from apps.leads.admin import LeadSourceAdmin
        from apps.leads.models import LeadSource
        admin_obj = LeadSourceAdmin(LeadSource, AdminSite())
        request = RequestFactory().get("/")
        request.user = self.superuser
        custom = LeadSource.objects.create(name="Promo", slug="promo")
        self.assertTrue(admin_obj.has_delete_permission(request, custom))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.leads.tests.LeadSourceAdminTests -v 2`
Expected: FAIL — `NoReverseMatch` (admin not registered) / `ImportError: LeadSourceAdmin`.

- [ ] **Step 3: Update `apps/leads/admin.py`**

Replace the whole file with:

```python
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from .models import Lead, LeadSource


@admin.register(LeadSource)
class LeadSourceAdmin(ModelAdmin):
    list_display = ("name", "slug", "lead_count", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    fields = ("name", "slug", "icon", "image", "color", "is_active", "order")

    @admin.display(description=_("Lidlar"))
    def lead_count(self, obj):
        return obj.leads.count()

    def get_readonly_fields(self, request, obj=None):
        # Built-in channels keep their slug (ad links depend on it).
        if obj and obj.is_protected:
            return ("slug",)
        return ()

    def get_prepopulated_fields(self, request, obj=None):
        if obj and obj.is_protected:
            return {}
        return self.prepopulated_fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_protected:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ("full_name", "phone", "course", "source", "status", "is_notified", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "source", "course", "created_at")
    search_fields = ("full_name", "phone")
    date_hierarchy = "created_at"
    autocomplete_fields = ("source",)
    readonly_fields = ("referrer", "is_notified", "created_at", "updated_at")
    list_per_page = 50
    fieldsets = (
        (None, {"fields": ("full_name", "phone", "course", "message", "status", "source")}),
        (None, {"fields": ("referrer", "is_notified", "created_at", "updated_at"),
                "classes": ("collapse",)}),
    )
```

> `autocomplete_fields = ("source",)` requires `LeadSourceAdmin.search_fields` — present above.

- [ ] **Step 4: Add the `CRM` sidebar group**

In `config/settings.py`, inside `UNFOLD["SIDEBAR"]["navigation"]`, add this group **immediately after** the `"Murojaatlar"` group (after its closing `},`):

```python
            {
                "title": _("CRM"),
                "items": [
                    {"title": _("Manbalar"), "icon": "hub",
                     "link": reverse_lazy("admin:leads_leadsource_changelist")},
                ],
            },
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test apps.leads.tests.LeadSourceAdminTests apps.leads.tests.LeadAdminTests -v 2`
Expected: PASS (changelist 200, protected not deletable, custom deletable, existing lead admin tests still green).

- [ ] **Step 6: Commit**

```bash
git add apps/leads/admin.py config/settings.py apps/leads/tests.py
git commit -m "feat(crm): LeadSource admin + CRM sidebar group; lead source filter"
```

---

## Task 5: Dashboard per-source stats block (period switch + count-up + copy-link)

**Files:**
- Modify: `apps/analytics/dashboard.py`
- Modify: `templates/admin/index.html`
- Test: `apps/analytics/tests.py`

**Interfaces:**
- Consumes: `LeadSource` (`is_active`, `name`, `image`, `brand_key`, `icon`, `color`, `build_link`), `Lead.source` (Task 1); `SiteConfig.get_solo().site_domain`.
- Produces: `context["source_stats"]` — list of `{name, count, percent, link, image, brand, icon, color}` sorted by `count` desc; `context["source_period"]` ∈ `{"today","30","all"}`.

- [ ] **Step 1: Write the failing tests**

In `apps/analytics/tests.py`, add (imports at top of the new test as needed):

```python
class DashboardSourceStatsTests(TestCase):
    """dashboard_callback builds per-source lead stats with a period filter."""

    def _ctx(self, period=None):
        from django.test import RequestFactory
        from apps.analytics.dashboard import dashboard_callback
        url = "/admin/" if not period else f"/admin/?source_period={period}"
        return dashboard_callback(RequestFactory().get(url), {})

    def test_source_stats_counts_leads(self):
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        Lead.objects.create(full_name="B", phone="+998901234568", source=tg)
        ctx = self._ctx()
        by_name = {s["name"]: s["count"] for s in ctx["source_stats"]}
        self.assertEqual(by_name["Telegram"], 2)
        self.assertEqual(ctx["source_period"], "all")

    def test_source_stats_link_and_percent(self):
        from apps.leads.models import Lead, LeadSource
        tg = LeadSource.objects.get(slug="telegram")
        Lead.objects.create(full_name="A", phone="+998901234567", source=tg)
        tg_row = next(s for s in self._ctx()["source_stats"] if s["name"] == "Telegram")
        self.assertIn("source=telegram", tg_row["link"])
        self.assertEqual(tg_row["percent"], 100)

    def test_source_period_today_is_recorded(self):
        self.assertEqual(self._ctx("today")["source_period"], "today")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test apps.analytics.tests.DashboardSourceStatsTests -v 2`
Expected: FAIL — `KeyError: 'source_stats'`.

- [ ] **Step 3: Add the CRM context in `dashboard.py`**

In `apps/analytics/dashboard.py`, inside `_build_context`, add this block **immediately before** the final `return context`:

```python
    # ---- CRM: leads per source (period-filtered) --------------------------
    from django.utils.translation import get_language

    from apps.leads.models import LeadSource
    from apps.siteconfig.models import SiteConfig

    period = request.GET.get("source_period", "all")
    if period == "today":
        src_leads = leads.filter(created_at__date=today)
    elif period == "30":
        src_leads = leads.filter(created_at__gte=last_30)
    else:
        period = "all"
        src_leads = leads
    counts = {
        row["source"]: row["total"]
        for row in src_leads.values("source").annotate(total=Count("id"))
    }
    total_src = sum(counts.values()) or 1
    try:
        domain = SiteConfig.get_solo().site_domain or request.get_host()
    except Exception:  # pragma: no cover - defensive
        domain = request.get_host()
    lang = get_language() or "uz"

    source_stats = []
    for s in LeadSource.objects.filter(is_active=True):
        c = counts.get(s.id, 0)
        source_stats.append({
            "name": s.name,
            "count": c,
            "percent": round(c * 100 / total_src),
            "link": s.build_link(domain, lang),
            "image": s.image.url if s.image else "",
            "brand": s.brand_key,
            "icon": s.icon or "hub",
            "color": s.color or "",
        })
    source_stats.sort(key=lambda x: x["count"], reverse=True)
    context["source_stats"] = source_stats
    context["source_period"] = period
```

Then in the `dashboard_callback` `except` fallback, add two `setdefault` lines alongside the others:

```python
        context.setdefault("source_stats", [])
        context.setdefault("source_period", "all")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test apps.analytics.tests.DashboardSourceStatsTests -v 2`
Expected: PASS (3 tests).

- [ ] **Step 5: Add the CRM block to the dashboard template**

In `templates/admin/index.html`, change the load line to include `ui`:

```html
{% load i18n unfold ui %}
```

Then insert this block **after** the `{# ---- Leads: trend + status ---- #}` grid `</div>` (the one that closes at line ~65) and **before** the `{# ---- Tables ---- #}` block:

```html
    {# ---- CRM: manbalar boʻyicha lidlar ---- #}
    <div class="mb-8">
        {% component "unfold/components/card.html" with title=_('Manbalar boʻyicha lidlar (CRM)') class="h-full" %}
            <div class="flex flex-wrap gap-1.5 mb-5 text-sm">
                <a href="?source_period=today" class="px-3 py-1.5 rounded-lg font-medium {% if source_period == 'today' %}bg-primary-600 text-white{% else %}bg-base-100 dark:bg-base-800 text-font-subtle-light dark:text-font-subtle-dark{% endif %}">{% translate "Bugun" %}</a>
                <a href="?source_period=30" class="px-3 py-1.5 rounded-lg font-medium {% if source_period == '30' %}bg-primary-600 text-white{% else %}bg-base-100 dark:bg-base-800 text-font-subtle-light dark:text-font-subtle-dark{% endif %}">{% translate "30 kun" %}</a>
                <a href="?source_period=all" class="px-3 py-1.5 rounded-lg font-medium {% if source_period == 'all' %}bg-primary-600 text-white{% else %}bg-base-100 dark:bg-base-800 text-font-subtle-light dark:text-font-subtle-dark{% endif %}">{% translate "Jami" %}</a>
            </div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {% for s in source_stats %}
                    <div class="flex items-center gap-4 rounded-lg border border-base-200 p-4 dark:border-base-800">
                        <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-base-100 dark:bg-base-800" style="{% if s.color %}color:{{ s.color }}{% endif %}">
                            {% if s.image %}<img src="{{ s.image }}" alt="{{ s.name }}" class="h-8 w-8 rounded object-contain">
                            {% elif s.brand %}{% social_icon s.brand size=26 %}
                            {% else %}<span class="material-symbols-outlined text-3xl">{{ s.icon }}</span>{% endif %}
                        </span>
                        <div class="min-w-0 flex-1">
                            <div class="flex items-center justify-between gap-2">
                                <span class="truncate font-semibold text-font-important-light dark:text-font-important-dark">{{ s.name }}</span>
                                <span class="text-lg font-bold text-primary-600 dark:text-primary-400" data-countup="{{ s.count }}">0</span>
                            </div>
                            <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-base-100 dark:bg-base-800">
                                <div class="h-full rounded-full bg-primary-500" style="width:{{ s.percent }}%"></div>
                            </div>
                            <div class="mt-2 flex items-center justify-between gap-2">
                                <span class="text-xs text-font-subtle-light dark:text-font-subtle-dark">{{ s.percent }}%</span>
                                <button type="button" data-copy-link="{{ s.link }}" class="inline-flex items-center gap-1 text-xs font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400">
                                    <span class="material-symbols-outlined text-base">content_copy</span>
                                    <span data-copy-label>{% translate "Havola" %}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                {% empty %}
                    <p class="text-sm text-font-subtle-light dark:text-font-subtle-dark">{% translate "Hali manba yoʻq." %}</p>
                {% endfor %}
            </div>
            <script>
                (function () {
                    function countUp(el) {
                        var target = parseInt(el.getAttribute("data-countup"), 10) || 0;
                        if (target <= 0) { el.textContent = "0"; return; }
                        var start = null, dur = 900;
                        function step(ts) {
                            if (!start) start = ts;
                            var p = Math.min((ts - start) / dur, 1);
                            el.textContent = Math.floor(p * target).toString();
                            if (p < 1) requestAnimationFrame(step);
                        }
                        requestAnimationFrame(step);
                    }
                    document.querySelectorAll("[data-countup]").forEach(countUp);
                    document.querySelectorAll("[data-copy-link]").forEach(function (btn) {
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
                                ta.value = link;
                                document.body.appendChild(ta);
                                ta.select();
                                try { document.execCommand("copy"); } catch (e) {}
                                document.body.removeChild(ta);
                                flash();
                            }
                        });
                    });
                })();
            </script>
        {% endcomponent %}
    </div>
```

> Note (CLAUDE.md): the `{# … #}` marker above is single-line — safe. Do not split it across lines.

- [ ] **Step 6: Manual verification**

Run: `python manage.py runserver 8001`, log into `/admin/`. Confirm the "Manbalar boʻyicha lidlar (CRM)" card renders with source cards, numbers animate from 0, the period tabs reload with `?source_period=…`, and clicking "Havola" copies `https://…/uz/#contact?source=…` (paste to check; label flips to ✓). Switch admin language and confirm the copied link's `/uz|ru|en/` prefix follows.

- [ ] **Step 7: Commit**

```bash
git add apps/analytics/dashboard.py templates/admin/index.html apps/analytics/tests.py
git commit -m "feat(crm): per-source lead stats on dashboard (period + count-up + copy link)"
```

---

## Task 6: Source in the Telegram notification

**Files:**
- Modify: `apps/leads/notifications.py`
- Test: `apps/leads/tests.py`

**Interfaces:**
- Consumes: `Lead.source` (Task 1).
- Produces: `_build_message(lead)` output contains a `🔗 Manba: <name>` line.

- [ ] **Step 1: Write the failing test**

In `apps/leads/tests.py`, add to the notifications test area (e.g. after `NotifyNewLeadTests`), a small class:

```python
class BuildMessageSourceTests(TestCase):
    """The Telegram message body names the lead's source."""

    def test_message_includes_source_name(self):
        from apps.leads.models import Lead, LeadSource
        from apps.leads.notifications import _build_message
        tg = LeadSource.objects.get(slug="telegram")
        lead = Lead.objects.create(
            full_name="A", phone="+998901234567", source=tg,
        )
        msg = _build_message(lead)
        self.assertIn("Manba", msg)
        self.assertIn("Telegram", msg)

    def test_message_source_falls_back_when_missing(self):
        from apps.leads.models import Lead
        from apps.leads.notifications import _build_message
        lead = Lead.objects.create(full_name="A", phone="+998901234567")
        lead.source = None  # force the fallback branch
        self.assertIn("Sayt", _build_message(lead))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test apps.leads.tests.BuildMessageSourceTests -v 2`
Expected: FAIL — `"Manba"` not found in the message.

- [ ] **Step 3: Add the source line to `_build_message`**

In `apps/leads/notifications.py`, inside `_build_message`, add the `source` variable near `course`/`message` and insert the line into `lines`:

```python
    course = html.escape(str(lead.course)) if lead.course else "—"
    message = html.escape(lead.message) if lead.message else "—"
    source = html.escape(lead.source.name) if lead.source else "Sayt"
    created = timezone.localtime(lead.created_at).strftime("%d.%m.%Y %H:%M")
    lines = [
        "<b>🆕 Yangi ariza</b>",
        "",
        f"👤 <b>Ism:</b> {html.escape(lead.full_name)}",
        f"📞 <b>Telefon:</b> {html.escape(lead.phone)}",
        f"📚 <b>Kurs:</b> {course}",
        f"💬 <b>Izoh:</b> {message}",
        f"🔗 <b>Manba:</b> {source}",
        f"🕒 <b>Vaqt:</b> {created}",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.leads.tests.BuildMessageSourceTests -v 2`
Expected: PASS (2 tests).

- [ ] **Step 5: Full suite + commit**

Run the affected suites to confirm nothing regressed:

Run: `python manage.py test apps.leads apps.analytics -v 1`
Expected: PASS (all leads + analytics tests green).

```bash
git add apps/leads/notifications.py apps/leads/tests.py
git commit -m "feat(crm): include lead source in Telegram notification"
```

---

## Self-Review

**Spec coverage:**
- Hidden `source` field on the form → Task 2 (input) + Task 3 (JS fill) ✓
- Defaults `site/telegram/instagram/facebook`, default `site` → Task 1 (data migration + `resolve`) ✓
- `#contact?source=…` links → Task 3 (hash parse) ✓
- Server accepts known source, else `site` → Task 2 + `LeadSource.resolve` ✓
- CRM section in Unfold → Task 4 (sidebar `CRM` group + Manbalar list) ✓
- Source icons + per-source counts with count-up → Task 5 ✓
- Admin creates new source (name→slug auto, icon/image) → Task 1 (fields) + Task 4 (`prepopulated_fields`, admin) ✓
- Link generated in the admin's current language → Task 5 (`get_language()` + `build_link`) ✓
- Copy-link button per source → Task 5 ✓
- Source shown in bot (Telegram) notification → Task 6 ✓

**Placeholder scan:** none — every step has concrete code/commands.

**Type consistency:** `LeadSource.resolve`, `get_default`, `build_link(domain, lang)`, `brand_key`, `DEFAULT_SLUG` defined in Task 1 and used identically in Tasks 2/5. `source_stats` dict keys (`name/count/percent/link/image/brand/icon/color`) match between Task 5 dashboard and template. `has_delete_permission` signature matches Task 4 test. `referrer` field name consistent across model/view/admin/tests.

## Manual QA checklist (after all tasks)
- [ ] `python manage.py test apps.leads apps.analytics` fully green.
- [ ] `/uz/#contact?source=instagram` → submit → new lead has `source=instagram` in admin.
- [ ] Unknown `?source=zzz` → lead `source=site`.
- [ ] CRM dashboard cards animate; copy button yields correct localized link; period tabs work.
- [ ] Telegram test message (if a bot token is configured) shows `🔗 Manba:`.
- [ ] Add a custom source in admin (name "Promo" → slug auto `promo`, pick a Material icon) → appears on dashboard; deleting `site` is blocked.
