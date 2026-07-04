# CRM — ariza manbasini (source) kuzatish

**Sana:** 2026-07-04
**Holat:** Tasdiqlangan (implementatsiyaga tayyor)

## Maqsad

Har xil ijtimoiy tarmoq / reklama kanallaridan kelayotgan arizalarni
(lidlarni) manbasi bo'yicha ajratib kuzatish. Reklama qilinganda "qaysi
kanaldan qancha lid kelyapti" degan savolga javob berish.

Ariza qoldirish formasiga **yashirin `source`** maydoni qo'shiladi. Reklama
havolalari `?source=<slug>` bilan tarqatiladi:

```
https://hopeschool.uz/uz/#contact?source=telegram
https://hopeschool.uz/uz/#contact?source=instagram
```

Standart (default) manba — `site`. Havolada mos keluvchi faol source kelsa,
o'sha olinadi; aks holda `site`.

**Standart 4 manba (built-in):** `site`, `telegram`, `instagram`, `facebook`.

## Muhim texnik cheklov: hash fragment

`#contact?source=telegram` da `?source=...` — **URL hash fragmenti** ichida.
Brauzer fragmentni serverga **yubormaydi**, shuning uchun serverdan
`request.GET["source"]` orqali o'qib bo'lmaydi. Manba **klient tomonda
JavaScript bilan** o'qilib, formadagi yashirin maydonga yoziladi va POST bilan
yuboriladi. JS ham `location.hash`, ham `location.search` dan o'qiydi (agar
kelajakda `?source=...#contact` ko'rinishi ham ishlatilsa).

## 1. Ma'lumotlar modeli — `apps/leads/models.py`

### `LeadSource` (yangi)

`OrderedActiveModel` dan meros oladi (`order`, `is_active`, `created_at`,
`updated_at` tayyor keladi).

| Maydon | Turi | Izoh |
|---|---|---|
| `name` | `CharField(max_length=80)` | Bitta umumiy nom ("Instagram", "Bahorgi aksiya"). Tarjima qilinmaydi (CRM ichki bo'lim). |
| `slug` | `SlugField(unique=True)` | Nomdan avtomatik (`prepopulated_fields`); qo'lda o'zgartirsa bo'ladi. Havolada shu ishlatiladi. |
| `icon` | `CharField(max_length=48, blank=True)` | Material Symbols nomi (masalan `public`). Rasm bo'lmaganda ishlatiladi. |
| `image` | `ImageField(upload_to="crm/sources/", blank=True)` | "Rasm (hisobot uchun)". Kartochkada ustunlik oladi. `image_validators`. |
| `color` | `CharField(max_length=7, blank=True)` | Kartochka aksenti (hex, `#RRGGBB`). Bo'sh bo'lsa primary rang. |
| `is_protected` | `BooleanField(default=False)` | Built-in 4 manba uchun `True` — o'chirilmaydi, slug o'zgartirilmaydi. |

**Kartochkada ikonka tanlash tartibi (`display_icon_html` / property):**
1. `image` yuklangan bo'lsa → rasm.
2. Aks holda, slug ma'lum brand'ga (`site`/`telegram`/`instagram`/`facebook`
   va shu kabi) mos kelsa → mavjud `social_icon` brand SVG (site → `website`).
3. Aks holda → Material Symbols `icon`.

**Yordamchi metodlar:**
- `LeadSource.get_default()` → `slug="site"` manbani `get_or_create` bilan
  qaytaradi (built-in o'chib ketgan bo'lsa ham xavfsiz).
- `LeadSource.resolve(slug)` → berilgan slug bo'yicha **faol** source; topilmasa
  `get_default()`. Serverda xom matndan himoya shu yerda.
- `build_link(domain, lang)` → `https://{domain}/{lang}/#contact?source={slug}`.

### `Lead` modeliga o'zgarish

- Mavjud `source` (CharField, UTM/referrer) → **`referrer`** deb qayta nomlanadi
  (`max_length=255`, `blank=True`). Ma'lumot yo'qolmaydi.
- Yangi `source = ForeignKey("leads.LeadSource", on_delete=SET_NULL,
  null=True, blank=True, related_name="leads", verbose_name=_("Manba"))`.

## 2. Migratsiyalar

1. **Schema migratsiya:** `LeadSource` yaratish; `Lead.source` (CharField) ni
   `Lead.referrer` ga `RenameField`; yangi `Lead.source` FK qo'shish.
2. **Data migratsiya** (`RunPython`, oldinga+orqaga):
   - 4 built-in yaratish: `site` (icon `public`), `telegram`, `instagram`,
     `facebook` — barchasi `is_protected=True`. `name`: "Sayt", "Telegram",
     "Instagram", "Facebook". `order`: 0..3.
   - Mavjud barcha leadlar `source` FK sini `site` ga backfill qilish (ular
     sayt formasidan kelgan). `referrer` allaqachon eski qiymatni saqlaydi.

> Data migratsiyada modelni `apps.get_model` orqali oling; `slugify` ni to'g'ri
> import qiling. Prod'da CI/CD avto-migrate qiladi (qo'lda migrate shart emas).

## 3. Forma va ular ishlashi

### Shablonlar
`templates/sections/_contact.html` va `templates/partials/_modal.html` — har
ikkala lead formasiga honeypot yonига yashirin maydon:

```html
<input type="hidden" name="source" value="site">
```

### JavaScript — `static/js/main.js`
Yangi kichik IIFE (mavjud `previewSubmit` yonida):
- Sahifa yuklanganda `location.hash` (`#contact?source=telegram`) va
  `location.search` dan `source` parametrini ajratib oladi.
- Topilsa `sessionStorage["lead_source"]` ga saqlaydi (sahifada yurса ham
  saqlanadi).
- `document.querySelectorAll('input[name="source"]')` — barchasiga qiymatni
  yozadi (default "site" saqlanadi, faqat topilganda almashtiradi).

### View — `apps/leads/views.py`
- `_capture_source(request)` → **`_capture_referrer(request)`** ga
  o'zgartiriladi (UTM `utm_source` yoki `HTTP_REFERER`, 255 belgigacha). Natija
  `lead.referrer` ga yoziladi.
- Yangi: POST'dagi `source` slug'ini `LeadSource.resolve(slug)` orqali hal
  qilib `lead.source` FK ga yoziladi (noma'lum → `site`).
- `LeadForm.Meta.fields` o'zgarmaydi (`full_name, phone, course, message`);
  `source`/`referrer` view'da qo'lda o'rnatiladi (hozirgi pattern kabi).

## 4. CRM — admin panel

### Sidebar — `config/settings.py` `UNFOLD["SIDEBAR"]`
Yangi guruh (mavjud "Murojaatlar" yonida yoki alohida):

```python
{
    "title": _("CRM"),
    "items": [
        {"title": _("Manbalar"), "icon": "hub",
         "link": reverse_lazy("admin:leads_leadsource_changelist")},
    ],
},
```

### `LeadSource` admin — `apps/leads/admin.py`
- `list_display`: nom (ikonka bilan), `slug`, lidlar soni, `is_active`, `order`.
- `prepopulated_fields = {"slug": ("name",)}`.
- Built-in himoyasi: `is_protected` bo'lsa `has_delete_permission=False` va
  `slug` readonly. `get_readonly_fields` da shartli.
- Maydonlar: `name`, `slug`, `icon`, `image`, `color`, `is_active`, `order`.

### Bosh dashboard bloki — `apps/analytics/dashboard.py` + `templates/admin/index.html`

**`dashboard_callback` ga qo'shiladi:**
- Davr: `request.GET.get("source_period")` ∈ {`today`, `30`, `all`}; default
  `all`. Mos `created_at` filtri.
- Har faol `LeadSource` bo'yicha lidlar soni (`Count`), ulush foizi.
- Har biri uchun havola: domen `SiteConfig.site_domain` (bo'lmasa
  `request.get_host()`), til `get_language()` → `source.build_link(...)`.
- `context["source_stats"]` = ro'yxat: `{name, slug, count, percent, link,
  image_url, icon_html, color}`.
- `context["source_period"]` (faol tab) va tab havolalari.
- Barchasi defensive `try/except` ichida (mavjud pattern) — jadval hali
  migrate bo'lmasa nol'ga tushadi.

**`index.html` — yangi blok** (grafiklar ostida):
- Davr tablari: **[Bugun] [30 kun] [Jami]** — `?source_period=today|30|all`
  havolalari (server-side reload).
- Kartochkalar grid: ikonka/rasm, nom, lidlar soni (`data-countup` bilan
  **count-up animatsiya**), ulush bari/foizi, **"Havolani nusxa olish"**
  tugmasi (`data-copy="<link>"`).
- Inline `<script>`: (a) `data-countup` ni 0 dan qiymatgacha `requestAnimation
  Frame` bilan animatsiya; (b) copy tugmasi `navigator.clipboard.writeText`,
  bosilganda "Nusxa olindi" holati (mavjud welcomemsg count-up patterniga mos).

## 5. Telegram bildirishnoma — `apps/leads/notifications.py`
`_build_message` ga qator qo'shiladi:

```python
source = html.escape(lead.source.name) if lead.source else "Sayt"
# ... lines ichiga:
f"🔗 <b>Manba:</b> {source}",
```

`notify_new_lead` post-commit thread'da ishlaydi, `lead.source` FK mavjud.

## 6. Testlar — `apps/leads/tests.py`
- **Yangilash:** `test_utm_source_captured` → endi `lead.referrer == "google"`.
- **Yangi testlar:**
  - Havolada `source=telegram` (POST hidden field) → `lead.source.slug ==
    "telegram"`.
  - Noma'lum slug (`source=xyz`) → `lead.source.slug == "site"`.
  - `source` bo'sh/berilmagan → default `site`.
  - `LeadSource.resolve()` faol bo'lmagan manbani rad etib `site` qaytaradi.
  - Protected source admin'da `has_delete_permission=False`.
  - `dashboard_callback` `source_stats` ni to'g'ri sanaydi (davr filtri bilan).
- Migratsiyadan keyin 4 built-in mavjudligi (data-migratsiya smoke testi).

## Qamrovdan tashqarida (YAGNI)
- Manba nomining ko'p tilliligi (uz/ru/en) — kiritilmaydi.
- Alohida CRM sahifasi/route — statistika bosh dashboardda.
- Manba bo'yicha vaqt grafigi (faqat sonlar + count-up).
- Klient tomonda AJAX davr filtri — server-side reload yetarli.

## Konvensiyalar (CLAUDE.md)
- Ko'p qatorli `{# … #}` **ishlatilmaydi** (sahifaga oqib chiqadi). Kerak bo'lsa
  `{% comment %}`.
- Dev server **8001**-portda: `python manage.py runserver 8001`.
