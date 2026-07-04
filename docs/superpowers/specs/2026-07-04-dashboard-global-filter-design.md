# Global dashboard vaqt filtri (Bugun/Hafta/Oy/Yil/Jami)

**Sana:** 2026-07-04
**Holat:** Tasdiqlangan (implementatsiyaga tayyor)

## Maqsad

Admin dashboard eng tepasiga yagona vaqt filtri qo'yiladi:
**[Bugun] [Hafta] [Oy] [Yil] [Jami]**. Bosilganda **AJAX** bilan faqat
dashboard kontenti yangilanadi (sahifa qayta yuklanmaydi) va barcha vaqtga
bog'liq widgetlar tanlangan davr bo'yicha qayta hisoblanadi.

Default davr: **Oy** (oxirgi 30 kun). Tanlov `sessionStorage`da saqlanadi.

## Periodlar va granularity

Period kalitlari: `today`, `week`, `month`, `year`, `all`.

| Period | Vaqt oynasi | Chiziqli grafik granularity | Nuqtalar |
|---|---|---|---|
| `today` | bugun (localdate) | soatlik | 24 (00–23) |
| `week` | oxirgi 7 kun | kunlik | 7 |
| `month` | oxirgi 30 kun | kunlik | ~30 |
| `year` | oxirgi 12 oy | oylik | 12 |
| `all` | birinchi yozuvdan hozirgacha | oylik | o'zgaruvchan |

Barcha oynalar `timezone` (Asia/Tashkent, `USE_TZ`) bo'yicha; bucketlash
`TruncHour`/`TruncDate`/`TruncMonth` bilan (TIME_ZONE'ga hurmat qiladi).
Gap-fill: bo'sh bucketlar `0` bilan to'ldiriladi.

Label formatlari: soatlik `"00".."23"`, kunlik `"dd.mm"`, oylik `"mm.yy"`.

## Qamrov

**Filtrga bo'ysunadi** (davr bo'yicha qayta hisoblanadi):
- KPI kartlari (pastda)
- Tashriflar grafigi (chiziqli, granularity + nuqta raqamlari)
- Arizalar grafigi (chiziqli, granularity + nuqta raqamlari)
- Qurilmalar (doughnut + legend)
- Davlatlar bo'yicha tashriflar (jadval)
- Top sahifalar (jadval)
- Top manbalar / referrerlar (jadval)
- Arizalar holati bo'yicha (jadval)
- CRM manba kartochkalari (**o'z Bugun/Hafta/30kun/Jami tablari olib tashlanadi**)

**Statik** (vaqtga bog'liq emas, filtrdan tashqarida):
- "Sayt kontenti" inventari (kurslar/o'qituvchilar/... umumiy sonlari)

**KPI to'plami** (davrga moslashadi):
- `Tashriflar (davr)` — tanlangan davrdagi tashriflar
- `Arizalar (davr)` — tanlangan davrdagi arizalar
- `Yangi arizalar (davr)` — davrda yaratilgan `status=new` arizalar
- `Kurslar / o'qituvchilar` — statik umumiy son

## Arxitektura

### 1. Ma'lumot qatlami — `apps/analytics/dashboard.py`
- **`build_dashboard_data(request, period)`** → barcha davrga bog'liq
  widgetlar uchun kontekst dict qaytaradi (KPIs, chart configlar, jadvallar,
  legend, source_cards). Ham sahifa yuklashda, ham AJAX view'da shu ishlatiladi
  (DRY). Butun tanasi defensive (jadval hali migrate bo'lmasa 500 bermaydi).
- **`_series(qs, period)`** → `(labels, counts)` — davr granularity bo'yicha
  `created_at`ni soat/kun/oy bucketlariga ajratadi va gap-fill qiladi.
- **`_period_window(period)`** → `(start_dt_or_None, granularity)` yordamchi.
- **`_line_chart_config(label, labels, series, color)`** → grafik uchun
  `<canvas data-chart>` ichiga joylanadigan JSON config (type, labels, datasets,
  displayLabels bayrog'i). Chart.js JS shuni o'qiydi.
- **`dashboard_callback(request, context)`** → `?period=` (default `month`) ni
  o'qib `build_dashboard_data`ni chaqiradi va kontekstga qo'shadi (sahifa
  yuklashda partial shu bilan render bo'ladi). Statik "content_inventory" shu
  yerda qoladi (partialdan tashqarida).

### 2. AJAX view — `apps/analytics/views.py` (yangi fayl)
```python
@staff_member_required
def dashboard_data(request):
    period = _clean_period(request.GET.get("period"))   # whitelist, default month
    context = build_dashboard_data(request, period)
    return render(request, "admin/_dashboard_content.html", context)
```
- `@staff_member_required` — faqat xodimlar (anonim → login redirect).
- HTML partialni qaytaradi (JSON emas) — DRY, bir template ikkala yo'l uchun.
- `render(request, ...)` — context processor'lar ishlashi uchun.
- `_clean_period` — noma'lum qiymat → `month`.

### 3. URL — `config/urls.py`
`admin.site.urls` include'idan **oldin** (yutib yuborilmasligi uchun), PWA
manifest patternidek:
```python
path(settings.ADMIN_URL + "dashboard-data/", dashboard_data, name="admin_dashboard_data"),
```

### 4. Shablonlar
- **`templates/admin/_dashboard_content.html`** (yangi) — barcha davrga bog'liq
  widgetlar: KPI kartlari, grafiklar (`<canvas data-dash-chart data-chart='…'>`),
  jadvallar (Unfold `table.html` komponenti), qurilma legend, CRM manba
  kartochkalari. Faqat Unfold-safe utility klasslar yoki inline style.
- **`templates/admin/index.html`** (o'zgartiriladi):
  - Tepada filtr paneli: `[Bugun][Hafta][Oy][Yil][Jami]` tugmalari
    (`data-period` + `?period=` href, progressive enhancement).
  - `<div id="dashboard-content">{% include "admin/_dashboard_content.html" %}</div>`.
  - Statik "Sayt kontenti" bloki `#dashboard-content`dan **tashqarida** (AJAX'da
    qayta render bo'lmaydi).
  - `admin_dashboard.js` yuklanadi.

### 5. Grafiklar — o'z Chart.js instansiyalari
Unfold chart komponenti AJAX'dan keyin qayta init bo'lmaydi (`renderCharts`
global emas), va doimiy nuqta raqamlari yo'q. Shuning uchun:
- Har grafik: `<canvas data-dash-chart data-chart='{...JSON...}'>`.
- **`static/js/admin_dashboard.js`**:
  - `initCharts(root)` — har `[data-dash-chart]` uchun eski instansiya bo'lsa
    `destroy`, so'ng `new Chart(ctx, config)`. Chart.js global (Unfold yuklaydi).
  - **Datalabels** — kichik inline plugin (`afterDatasetsDraw`): chiziqli
    grafikda har nuqta ustiga qiymat chizadi; nuqtalar zich bo'lsa (masalan >16)
    har `ceil(n/12)`-chisini ko'rsatadi (tiqilib ketmaslik uchun).
  - Ranglar Unfold CSS o'zgaruvchilaridan (`--color-primary-500` va h.k.),
    hozirgi dashboard uslubidek.
  - Instansiyalar registri (`destroy` uchun) — xotira sizib ketmasligi uchun.
- **Filtr JS**: tab bosilsa `fetch(ADMIN + "dashboard-data/?period=X")` →
  `#dashboard-content` `innerHTML` almashtiriladi → `initCharts(container)` →
  active tab yangilanadi → `sessionStorage`ga yoziladi. Yuklanayotganда konteyner
  ozroq shaffoflashadi.
  - JS o'chsa: tugmalar `?period=` havolasi bilan oddiy reload qiladi;
    `dashboard_callback` `?period=`ni o'qigani uchun bir xil natija.

### 6. Xatoliklar
- `build_dashboard_data` — `try/except` bilan himoyalangan (hozirgi
  `dashboard_callback` uslubi); xatoda bo'sh/nol qiymatlar.
- AJAX view — `build_dashboard_data` defensive bo'lgani uchun har doim 200 HTML.
- JS `fetch` xato bo'lsa — eski kontent qoladi, kichik xabar ko'rsatiladi,
  active tab tiklanadi.

## Testlar (`apps/analytics/tests.py`)
- `_series` bucketlash: soatlik (bugun), kunlik (hafta/oy), oylik (yil/jami) —
  `created_at`ni `.update()` bilan orqaga surib tekshirish (auto_now_add'ni
  chetlab). Gap-fill 0 tekshiruvi.
- `build_dashboard_data(period)`: har davr uchun to'g'ri sonlar va kutilgan
  kalitlar (kpis, visits_chart config, leads_chart config, device_*, tables,
  source_cards).
- CRM manba kartochkalari davr bo'yicha (mavjud mantiq, endi global davr
  boshqaradi) — noaktiv manba kartada yo'q, foiz faol manbalar bo'yicha.
- `dashboard_data` view: anonim → 302/403; xodim → 200 HTML (kutilgan markerlar
  bor); noma'lum `period` → `month`.
- Mavjud `DashboardSourceCardsTests` yangilanadi (endi `build_dashboard_data`
  orqali, global period bilan).

## Fayl tuzilmasi

| Fayl | Vazifa | Amal |
|---|---|---|
| `apps/analytics/dashboard.py` | `build_dashboard_data` + `_series` + chart config; `dashboard_callback` delegatsiya | O'zgartirish |
| `apps/analytics/views.py` | `dashboard_data` AJAX view | Yaratish |
| `config/urls.py` | `dashboard-data/` URL (admin ostida) | O'zgartirish |
| `templates/admin/_dashboard_content.html` | davrga bog'liq widgetlar partiali | Yaratish |
| `templates/admin/index.html` | filtr paneli + `#dashboard-content` + JS | O'zgartirish |
| `static/js/admin_dashboard.js` | chart init + AJAX filtr | Yaratish |
| `config/settings.py` | `UNFOLD["SCRIPTS"]`ga `admin_dashboard.js` | O'zgartirish |
| `apps/analytics/tests.py` | series/view/data testlari | O'zgartirish |

## Qamrovdan tashqarida (YAGNI)
- Foydalanuvchi tanlagan ixtiyoriy sana oralig'i (date range picker) — yo'q,
  faqat 5 ta tayyor davr.
- Real-time / avtoyangilanish — yo'q.
- Grafiklarni eksport qilish — yo'q.
- "Content inventory"ni davr bo'yicha filtrlash — yo'q (statik).

## Konvensiyalar (CLAUDE.md)
- Ko'p qatorli `{# … #}` ishlatilmaydi (sahifaga oqib chiqadi) — bir qatorli yoki
  `{% comment %}`.
- Dev server **8001**-portda.
- **Admin Tailwind cheklovi:** admin faqat Unfold'ning tayyor CSS'idan
  foydalanadi — yangi markuplarda faqat Unfold ishlatadigan utility klasslar yoki
  inline style (masalan `place-items-center`, `mt-2.5`, `object-contain`,
  arbitrary `transition-[width]`, `duration-500` **yo'q**; `flex items-center
  justify-center`, `mt-2`, `object-cover`, `transition-all` **bor**). Yangi
  klass ishlatishdan oldin `unfold/static/unfold/css/styles.css`da borligini
  tekshirish.
