# Partners section — admin-editable, 3-language design

**Status:** approved, implementation deferred ("keyinroq qilamiz").

## Problem

`templates/sections/_partners.html` is a hardcoded, non-translated marquee of
plain-text partner names (Cambridge, IELTS, Pearson, Khan Academy, Coursera,
Oxford, British Council). Changing it requires editing the template — no
admin UI, no per-language content, no way to add/remove/reorder a partner
without a code change.

## Scope

This spec covers only the Partners section. Other UI/UX improvements the user
may raise later are explicitly out of scope here and will get their own spec.

## Decisions (from clarifying questions)

- **Logo vs. text**: stay text-only, matching the current look. No logo image
  field — just make the existing text-name marquee admin-editable.
- **Translation**: `name` is per-language translatable (uz/ru/en) via
  `modeltranslation`, matching every other admin content model in this
  codebase (`WhyUsItem`, `StatItem`, ...), even though most current partner
  names are brand names that read the same in all three languages. Costs
  nothing for those; covers a future partner whose name should differ by
  language.
- **Link**: add an optional `website_url` field. Template wraps the name in
  `<a href="...">` only when set.

## Design

### Model — `apps/pages/models.py`, next to `WhyUsItem`

```python
class Partner(OrderedActiveModel):
    name = models.CharField(_("Nomi"), max_length=80)
    website_url = models.URLField(_("Veb-sayt (ixtiyoriy)"), blank=True)

    class Meta(OrderedActiveModel.Meta):
        verbose_name = _("Hamkor")
        verbose_name_plural = _("Hamkorlar")

    def __str__(self):
        return self.name
```

`order` / `is_active` come from `OrderedActiveModel` (already provides
admin-side reordering and a show/hide toggle).

### Translation — `apps/pages/translation.py`

```python
@register(Partner)
class PartnerTR(TranslationOptions):
    fields = ("name",)
```

### Admin — `apps/pages/admin.py`, mirroring `WhyUsItemAdmin`

```python
@admin.register(Partner)
class PartnerAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "website_url", "is_active", "order")
    list_editable = ("website_url", "is_active", "order")
```

Gets the auto-translate submit-line button + bulk action for free from
`AutoTranslateAdminMixin`, same as every other translated admin.

### View — `apps/pages/views.py`

Add to `LandingView.get_context_data`:

```python
ctx["partners"] = Partner.objects.filter(is_active=True)
```

(`_partners.html` is only included from `templates/pages/landing.html` —
verified via grep, no other template references it.)

### Template — `templates/sections/_partners.html`

Replace the two hardcoded `<span>` rows with two `{% for p in partners %}`
loops over the same queryset — preserves the current seamless-scroll marquee
technique (the track is the list duplicated back-to-back so the CSS animation
loops without a visible seam). Each name optionally wrapped in
`<a href="{{ p.website_url }}">` when `p.website_url` is set. Whole section
wrapped in `{% if partners %}` so it disappears cleanly (no empty bar) if the
admin empties the list.

### Migration

One `makemigrations pages` — picks up the model fields AND the
`name_uz`/`name_ru`/`name_en` columns in the same migration, since
modeltranslation patches the model class before `makemigrations` introspects
it (same one-shot pattern already used for `GalleryImage`, see the NOTE in
`apps/gallery/translation.py`).

Plus a **data migration** seeding the current 7 names (Cambridge, IELTS,
Pearson, Khan Academy, Coursera, Oxford, British Council) with empty
`website_url`, so the site doesn't go blank the moment this deploys. Admin
fills in URLs later if wanted.

### Tests

- Model: `__str__`, default ordering.
- Admin: changelist and add-view load (200).
- `LandingView`: context includes `partners`.
- Template: renders names; renders a link only when `website_url` is set;
  empty queryset hides the whole section (no `<div class="bg-alt...">`
  emitted).

### i18n build

`name`'s admin label ("Nomi") and the model's verbose names are plain Python
`gettext_lazy` strings already covered by Django's own admin-string
translation flow (`TabbedTranslationAdmin` + `AutoTranslateAdminMixin`) — no
new UI strings requiring a `locale/_build_catalogs.py` re-run.

## Alternatives considered (rejected)

- **JSON field on a singleton + custom admin widget** — reinvents what a
  plain model + admin list already gives for free (reordering, translation,
  add/remove); more code to build and maintain.
- **Fold into `SocialLink` with a `kind` discriminator** — conflates two
  unrelated concepts (social platforms vs. partner organizations) into one
  model/table, forces conditional branching into every place `SocialLink` is
  already consumed (footer, JSON-LD).

## Next step

Implementation deferred at the user's request. When resumed: invoke
`writing-plans` off this spec to produce the implementation plan, then
execute.
