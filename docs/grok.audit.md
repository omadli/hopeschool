# Hope School — to‘liq audit hisoboti

**Sana:** 2026-07-20  
**Auditor:** Grok (xAI)  
**Loyiha:** Hope School — Django 5.2 marketing sayti + Unfold admin + analitika/CRM  
**Scope:** over-engineering (ponytail), xavfsizlik, performance, UI/UX, usability  
**Metod:** kod/template/deploy konfiguratsiya tahlili (runtime Lighthouse/penetration test emas)

---

## 1. Qisqa xulosa

Hope School — kichik o‘quv markazi uchun **yaxshi arxitekturalangan**, production-ga tayyorlash chuqur o‘ylangan loyiha. Xavfsizlik (HTTPS/HSTS, axes, SSRF-guard, map embed sanitizer, obfuscated admin URL) va frontend (WebP, self-hosted fonts, responsive images) bo‘yicha o‘rtacha marketing saytdan ancha oldinda.

Asosiy xavflar/yaxshilashlar:

| Soha | Holat | Eng muhim nuqta |
|------|--------|------------------|
| Xavfsizlik | Yaxshi | CSP hali enforce qilinmagan; CKEditor `|safe` trust modeli; `/ariza/` CSRF-exempt |
| Performance | Yaxshi | Landing ~10+ query; VisitLog har GETda yozadi; SQLite scale cheklovi |
| UI/UX | Yaxshi | Modal focus trap yo‘q; reduced-motion yo‘q; phone default placeholder |
| Usability | Yaxshi | Admin matnlari boy; lead form phone mask yo‘q; til menyusi a11y |
| Over-engineering | O‘rtacha | Generator/scrap/docs yog‘i; o‘qilmaydigan maydonlar; 1 o‘lik dep |

**Umumiy ball (subyektiv, 10 dan):**

| Soha | Ball |
|------|------|
| Xavfsizlik | **8.0** |
| Performance | **7.5** |
| UI/UX | **7.5** |
| Usability | **8.0** |
| Kod soddaligi | **7.0** |
| **Umumiy** | **~7.6** |

---

## 2. Kuchli tomonlar (saqlash kerak)

- Production fail-fast: `DEBUG=False` da yaroqsiz `SECRET_KEY` / `ALLOWED_HOSTS=*` → `ImproperlyConfigured`
- `check --deploy` toza (test bilan tasdiqlangan: `apps/common/test_deploy.py`)
- Admin login: django-axes (IP+username lockout) + nginx `hs_login` zone
- Lead form: Origin check, honeypot, IP rate-limit (app + nginx), trusted-proxy-aware `client_ip`
- Certificate import: SSRF guard (`is_public_ip` + redirect re-validation + byte cap)
- Map embed: `nh3` + host allowlist (`sanitize_map_embed`)
- CKEditor: `sourceEditing` o‘chirilgan (stored XSS riskini kamaytiradi)
- Superuser himoyasi: admin orqali superuser yaratish/o‘chirish cheklangan
- Static: WhiteNoise manifest + gzip_static; self-hosted fonts (Google Fonts FOIT yo‘q)
- Images: easy-thumbnails WebP + width/height (CLS himoyasi)
- i18n: modeltranslation + admin avto-tarjima (review step bilan)
- Solo cache + context cache (`social_links`, `lead_courses`)
- Analytics: bot/staff/private IP filter; geo IP request pathdan tashqarida
- Deploy: fail2ban, prune-visitlogs timer, gunicorn worker recycle

---

## 3. Xavfsizlik (Security)

### 3.1. Yaxshi amaliyotlar

| Nazorat | Joylashuv | Izoh |
|---------|-----------|------|
| HTTPS/HSTS/secure cookies | `config/settings.py` | Faqat `DEBUG=False` |
| Brute-force | django-axes + nginx | Admin login |
| Admin path obfuscation | `ADMIN_URL` | robots.txt haqiqiy pathni oshkor qilmaydi |
| Upload limits | validators + `DATA_UPLOAD_MAX_*` | Rasm 5MB, video 50MB, PDF 10MB |
| Trusted proxy IP | `TRUSTED_PROXY_COUNT` | Rate-limit spoofing himoyasi |
| Telegram token write-only | `SiteConfigForm` | Token sahifada qayta ko‘rinmaydi |
| Analytics ID validators | regex | Inline script injection yopilgan |
| User admin hardening | `apps/common/admin.py` | Superuser escalate yo‘q |

### 3.2. Topilmalar (severity)

#### [SEC-1] Content-Security-Policy enforce qilinmagan — **O‘rta**

`deploy/hopeschool.uz.conf` da CSP faqat kommentariyada (Report-Only bo‘lib turibdi). XSS yoki yomon third-party skript bo‘lsa, brauzer cheklamaydi.

**Tavsiya:** staged rollout (Report-Only → console toza → enforce). CSP qoralmasi faylda tayyor.

#### [SEC-2] CKEditor maydonlari `|safe` render — **O‘rta** (trust model)

`course.description`, `post.body`, `teacher.bio`, `about.body` — admin HTML ishonchli deb olinadi. `sourceEditing` yo‘q, lekin:

- mediaEmbed iframe (YouTube va boshqalar) ruxsat etilgan
- buzilgan/compromised admin akkaunt → stored XSS mumkin
- server-side HTML sanitizer (nh3) faqat map embed uchun, rich text uchun emas

**Tavsiya:** public render oldidan CKEditor HTML ni allowlist bilan sanitize qilish (map embed kabi). Yoki staff-only trusted modelni hujjatlashtirish + 2FA (Django o‘zida yo‘q — tashqi).

#### [SEC-3] `/ariza/` CSRF-exempt — **Past–O‘rta** (hujjatlangan tradeoff)

`lead_create` CSRF-siz: stale token 403 muammosini bartaraf qilish uchun. Himoya: Origin, honeypot, rate-limit.

**Qoldiq xavf:** Origin yo‘q non-browser client spam; honeypot oddiy (`website` nomi).

**Tavsiya:** double-submit cookie yoki short-lived form token (session-less); honeypot nomini kamroq taxmin qilinadigan qilish; ixtiyoriy captcha (faqat 429 dan keyin).

#### [SEC-4] Media fayllar to‘g‘ridan-to‘g‘ri serve — **Past**

`/media/` nginx orqali ochiq. Admin yuklagan PDF/rasm/video public URL. Sertifikat PDF lar sezgir bo‘lishi mumkin (o‘quvchi ismi).

**Tavsiya:** sezgir PDF larni auth orqali yoki signed URL; yoki faqat render qilingan JPEG ko‘rsatish (hozir asosan shunday).

#### [SEC-5] VisitLog IP saqlash — **Past** (privacy)

Har tashrifda IP + UA yoziladi. GDPR/PD nazaridan: retention bor (`prune-visitlogs`), lekin privacy policy sahifasi yo‘q.

**Tavsiya:** public privacy/cookie notice (GA/Yandex bo‘lsa majburiyroq); IP hashing yoki qisqa retention (masalan 90 kun aniq sozlangan).

#### [SEC-6] Telegram bot token admin DB da — **Past**

Token DB da (write-only UI). DB backup oshkor bo‘lsa — token oqadi.

**Tavsiya:** production da tokenni faqat env da saqlash yoki encrypted field; backup access cheklash.

#### [SEC-7] `DEBUG` default True — **Past** (dev)

`.env.example` da `DEBUG=True` — to‘g‘ri. Production checklistga tayanadi.

**Tavsiya:** deploy docs da “DEBUG=False birinchi qator” ni bold qilib qoldirish (allaqachon bor).

### 3.3. Xavfsizlik — nima qilinmasin

- CSRF ni lead formga “shunchaki qaytarish” — UX regressiya (hujjatlangan)
- PyMuPDF (AGPL) qaytarish — litsenziya xavfi
- `ALLOWED_HOSTS=*` production da — allaqachon bloklangan

---

## 4. Performance

### 4.1. Yaxshi amaliyotlar

- Self-hosted WOFF2 fonts (latin + cyrillic subset)
- Tailwind CLI, no Node runtime
- WebP `<picture>` + lazy/eager/fetchpriority
- Hero LCP: `eager` + `fetchpriority=high`
- Solo LocMemCache + context TTL 60s
- Shared DatabaseCache for rate-limit (worker-lar bo‘ylab to‘g‘ri)
- Static: immutable 1y cache; media 30d
- gzip_static; brotli izoh bilan tayyor
- VisitLog: try/except — analytics response ni sindirmaydi
- GeoIP offline batch (request path emas)
- Gunicorn: kam worker (SQLite), `max_requests` recycle

### 4.2. Topilmalar

#### [PERF-1] Landing page ko‘p query — **O‘rta**

`LandingView` + `site_context`:

- 3× solo (cached)
- social_links, lead_courses (cached)
- about, home_video, stats, why_us, partners, courses, news, teachers, certificates, testimonials, gallery

Taxminan **10–15 DB hit** cold cache da. Kontent kichik bo‘lsa OK; traffic oshsa seziladi.

**Tavsiya:**

1. Landing context ni bitta `cache.get_or_set("landing:v1:{lang}", …, 60)` ga yig‘ish  
2. Yoki section larni template fragment cache  
3. `only()` / `defer("description")` — landing da CKEditor body kerak emas

#### [PERF-2] VisitLog synchronous INSERT har public GET — **O‘rta**

Middleware response dan keyin `VisitLog.objects.create(...)`. SQLite + 3 gunicorn worker → write contention mumkin.

**Tavsiya (tartib bo‘yicha):**

1. Hozirgi holat kichik traffic uchun yetarli  
2. Keyin: buffer (cache list + cron flush) yoki async task  
3. Scale bo‘lsa: PostgreSQL + connection pooling  

Prune weekly — yaxshi; lekin yuqori traffic da jadval tez o‘sadi.

#### [PERF-3] Thumbnail first-hit cost — **Past–O‘rta**

easy-thumbnails birinchi so‘rovda generate qiladi. Ko‘p rasmli landing → birinchi tashrif sekinroq.

**Tavsiya:** deploy/post-save da thumbnail prewarm; yoki admin save signal.

#### [PERF-4] Admin dashboard og‘ir agregatsiyalar — **Past**

`build_dashboard_data` bir nechta `Count`/`Trunc*` — faqat staff, kam chaqiriladi. AJAX period switch bor.

**Tavsiya:** kerak bo‘lsa period natijalarini qisqa cache (30–60s).

#### [PERF-5] Dual map iframes — **Past**

Koordinata rejimida Google + Yandex iframe birga yuklanadi (biri `hidden`).

**Tavsiya:** faqat faol tab iframe src ni lazy set qilish.

#### [PERF-6] SQLite ceiling — **Ma’lum cheklov**

WAL + IMMEDIATE + kam worker — ongli tanlov. Analitika yozuvi + lead + session o‘sishi bilan bottleneck.

**Tavsiya:** traffic >~50–100 concurrent yoki VisitLog million+ → Postgres reja.

#### [PERF-7] Third-party analytics — **Past**

GA4 + Yandex Metrica (agar yoqilgan) — main threadga tashqi skript.

**Tavsiya:** `defer`/Partytown ixtiyoriy; yoki faqat bitta analytics.

### 4.3. Core Web Vitals (kutilayotgan)

| Metric | Kutilayotgan | Asos |
|--------|--------------|------|
| LCP | Yaxshi | hero WebP + fetchpriority, self-hosted fonts |
| CLS | Yaxshi | width/height on images |
| INP | Yaxshi | yengil vanilla JS |
| TTFB | O‘rtacha | Django + SQLite + cold queries |

---

## 5. UI / UX

### 5.1. Yaxshi tomonlar

- Aniq brand (ko‘k/qizil), dark mode, sticky header
- Mobile bottom bar: qo‘ng‘iroq + ariza (conversion)
- Scroll reveal, count-up, carousels — marketing sayt uchun mos
- Skip link, asosiy CTA lar qizil pill
- Certificate lightbox, map Google/Yandex toggle
- Toast success feedback
- Admin Unfold + dashboard KPI/charts
- PWA manifest (public + admin alohida)

### 5.2. Topilmalar

#### [UX-1] Modal: focus trap va focus restore yo‘q — **O‘rta (a11y)**

`#modal` ochilganda focus birinchi maydonga o‘tmaydi; Tab fon elementlariga chiqishi mumkin; yopilganda trigger ga qaytmaydi.

**Tavsiya:** ochilganda focus first input; focus trap; Escape allaqachon bor; yopilganda `[data-open-modal]` ga focus.

#### [UX-2] `prefers-reduced-motion` e’tiborsiz — **Past–O‘rta**

Carousel autoplay, floaty animation, count-up, scroll progress — reduced-motion da to‘xtatilmaydi.

**Tavsiya:**

```css
@media (prefers-reduced-motion: reduce) {
  .sr, .floaty, .count { animation: none !important; }
}
```

JS da autoplay `matchMedia('(prefers-reduced-motion: reduce)')` bilan o‘chirish.

#### [UX-3] Til dropdown a11y — **Past**

`aria-haspopup` bor, lekin `aria-expanded` yo‘q; Escape yopmaydi; roving tabindex yo‘q.

**Tavsiya:** `aria-expanded` toggle; Escape close; arrow keys ixtiyoriy.

#### [UX-4] Burger menyu `aria-expanded` yo‘q — **Past**

`aria-controls="drawer"` bor, holat e’lon qilinmaydi.

#### [UX-5] Telefon placeholder vs haqiqiy mask — **O‘rta (conversion)**

Placeholder `+998 __ ___ __ __`, lekin input mask/auto-format yo‘q. Foydalanuvchi `90 123 45 67` yuborsa — server rad etishi mumkin (`+998` majburiy).

**Tavsiya:** oddiy JS mask yoki blur da `normalize_phone` ga o‘xshash formatlash; xato matnini maydon ostida ko‘rsatish (hozir umumiy error).

#### [UX-6] Mobile bar default telefon — **Past**

```html
tel:{{ site_config.phone_primary|default:'+998901234567' }}
```

Admin telefon bo‘sh bo‘lsa — soxta raqamga chaqiruv.

**Tavsiya:** bo‘sh bo‘lsa tugmani yashirish yoki faqat ariza CTA qoldirish.

#### [UX-7] Form xatolari maydonga bog‘lanmagan — **Past–O‘rta**

API field errors qaytaradi; JS faqat birinchi message ni umumiy `data-form-error` ga yozadi. Qaysi maydon xato ekanligi aniq emas.

**Tavsiya:** `aria-invalid` + maydon ostidagi xabar.

#### [UX-8] Carousel: faqat mouse/touch pause — **Past**

Keyboard/screen reader foydalanuvchisi uchun pause yo‘q; autoplay doimiy.

**Tavsiya:** reduced-motion + hover/focus pause.

#### [UX-9] Map: yandex manual embed o‘qilmaydi — **Past (bug/UX)**

Admin da `yandex_maps_embed` bor; template faqat `safe_google_maps_embed` ni tekshiradi. Operator Yandex embed kiritishi mumkin — natija ko‘rinmaydi.

**Tavsiya:** ikkalasini qo‘llash yoki maydonni olib tashlash (ponytail bilan mos).

#### [UX-10] Dark mode flash himoyasi bor — yaxshi

Inline theme script paint oldidan ishlaydi — saqlansin.

---

## 6. Usability (foydalanish qulayligi)

### 6.1. Public sayt

| Vazifa | Holat | Izoh |
|--------|--------|------|
| Kurs ko‘rish | Yaxshi | Home section + detail |
| Ariza yuborish | Yaxshi | Modal + contact form + mobile bar |
| Qo‘ng‘iroq | Yaxshi | Mobile tel button |
| Til almashtirish | Yaxshi | URL prefix `/uz/` `/ru/` `/en/` |
| Sertifikat ko‘rish | Yaxshi | Lightbox + tashqi havola |
| Galereya/video | Yaxshi | Bitta video play |
| SEO/share | Yaxshi | meta, OG, sitemap, JSON-LD |

**Kamchiliklar:**

- [USE-1] Lead source URL (`#contact?source=telegram`) non-standard hash query — ishlaydi (JS), lekin oddiy foydalanuvchi/share ba’zan chalkash. Alternativa: `?source=` query (server ham ko‘radi).
- [USE-2] Bo‘sh bo‘limlar (kurs yo‘q, galereya bo‘sh) — empty state dizayni bo‘limga qarab farq qiladi; seed_demo yordam beradi.
- [USE-3] Privacy / oferta / qayta ishlash sahifalari yo‘q — ota-onalar ishonchi uchun foydali.

### 6.2. Admin (operator)

| Vazifa | Holat |
|--------|--------|
| Kontent tahrirlash | Yaxshi — Unfold, tabbed i18n |
| Avto-tarjima UZ→RU/EN | Yaxshi — review warning |
| Arizalar CRM | Yaxshi — status, source badge |
| Dashboard | Yaxshi — period filter, CRM cards |
| Sertifikat import (QR/URL) | Yaxshi — maxsus pipeline |
| Xarita picker | Yaxshi — Leaflet self-hosted |
| Telegram sozlash | Yaxshi — multi recipient |

**Kamchiliklar:**

- [USE-4] Sidebar bo‘limlari ko‘p (“Bosh sahifa bloklari” 6 ta) — yangi admin uchun o‘rganish egri chizig‘i. `docs/ADMIN.md` bor — yaxshi.
- [USE-5] `is_featured` (news, testimonials) admin da bor, saytda ishlatilmaydi — operator chalkashishi mumkin.
- [USE-6] Dual Telegram (.env + panel) — status ko‘rsatiladi, lekin yangi operator uchun murakkab.
- [USE-7] Dual map (lat/lng vs embed) — docs admin da bor; shunga qaramay chalkashlik mumkin.

### 6.3. Deploy / ops usability

- `docs/ORNATISH.md`, `JOYLASHTIRISH.md`, `.env.example` — yaxshi
- `createcachetable` migration orqali — yaxshi (unutish xavfi kam)
- CSP “manual copy to server” — CI yo‘q; odam xatosi mumkin

---

## 7. Over-engineering audit (ponytail)

> Scope: faqat ortiqcha murakkablik. Format: `<tag> nima. o‘rniga. [path]`

`delete:` `locale/_build_catalogs.py`, `_build_uz_admin.py`, `_extra_translations.py`, `_gen_translations.py`, `_make_extra.py`, `_verify.py`, `_draft_translations.txt` — bir martalik katalog generatorlari; `.po`/`.mo` bor. Faqat `manage.py compilemo` qoldiring. [`locale/`]

`delete:` `docs/superpowers/plans/*` va `specs/*` — ship bo‘lgan feature rejalari. Git history yetarli. [`docs/superpowers/`]

`delete:` `_scratch/` (`fetch_hope.py` + `posts.json`) — scrap/dev dump. [`_scratch/`]

`delete:` `django-import-export` — hech qayerda import yo‘q, `INSTALLED_APPS` da yo‘q. [`requirements.txt`]

`delete:` `NewsPost.is_featured` va `Testimonial.is_featured` — public query filterlamaydi. [`apps/news/models.py`, `apps/testimonials/models.py`]

`delete:` `SiteConfig.google_map_src`, `yandex_map_src`, `google_maps_link`, `yandex_maps_link` — template `ui` taglarini ishlatadi; link property lar o‘lik. [`apps/siteconfig/models.py`]

`delete:` `yandex_maps_embed` + `safe_yandex_maps_embed` — template o‘qimaydi (faqat google embed). [`apps/siteconfig/models.py`, `templates/sections/_contact.html`]

`yagni:` ikki xil xarita manbasi (lat/lng avto + qo‘lda embed). Lat/lng + Leaflet yetadi. [`apps/siteconfig/`]

`yagni:` Telegram dual config (admin + `.env` fallback). Panel to‘ldirilgach fallback ni soddalashtirish. [`apps/leads/notifications.py`, `config/settings.py`]

`yagni:` `fill_translations()` serial API — production faqat `fill_translations_bulk`. [`apps/common/translation.py`]

`yagni:` `AboutSection` OrderedActive, lekin view `.first()`. `SingletonModel` qiling. [`apps/pages/models.py`]

`shrink:` uchta deyarli bir xil Sitemap klassi → bitta `ModelSitemap`. [`apps/common/sitemaps.py`]

`shrink:` `leads.views._client_ip` → to‘g‘ridan `client_ip(...) or "unknown"`. [`apps/leads/views.py`]

`yagni:` `LeadSource.color` — CRM polish; brand icon yetishi mumkin. [`apps/leads/models.py`]

**net (ponytail): ~−5.5k lines (docs+scratch+locale generators asosiy), −1 dep possible.**

### 7.1. O‘chirilmasin (asosli murakkablik)

| Qism | Sabab |
|------|--------|
| `apps/common/translation.py` | Haqiqiy admin MT feature |
| `certificates/services.py` | SSRF-aware PDF import |
| Analytics middleware + dashboard | Product surface |
| `OrderedActiveModel` / `VideoMixin` | Ko‘p modelda |
| axes, nh3, polib, solo, pypdfium2 | Aniq vazifa |
| Testlar (~3.3k LOC) | Coverage, bloat emas |

---

## 8. Prioritetli harakatlar rejasi

### P0 — tez / yuqori foyda (1–2 kun)

1. **[UX-6]** Mobile bar: bo‘sh telefonda soxta `tel:` ni olib tashlash  
2. **[UX-9] / ponytail** Yandex embed path ni tuzatish yoki maydonni o‘chirish  
3. **[delete]** `django-import-export` ni requirements dan olib tashlash  
4. **[delete]** `_scratch/` ni repodan chiqarish (agar kerak emas)  
5. **[UX-5]** Telefon input: blur da normalizatsiya yoki oddiy mask  

### P1 — muhim (1 hafta)

6. **[SEC-1]** CSP Report-Only → enforce (nginx)  
7. **[UX-1]** Modal focus trap + initial focus  
8. **[PERF-1]** Landing fragment/cache yoki `only()` optimizatsiya  
9. **[UX-2]** `prefers-reduced-motion`  
10. **[delete]** o‘lik `is_featured` maydonlar yoki ularni haqiqatan filterlash  

### P2 — o‘rta muddat

11. **[SEC-2]** Rich text public sanitize (nh3 allowlist)  
12. **[PERF-2]** VisitLog yozuvini yengillashtirish (agar traffic oshsa)  
13. **[PERF-5]** Map iframe lazy-load  
14. **[USE-3]** Privacy / cookie banner (agar GA/Yandex yoqilsa)  
15. **[ponytail]** locale generatorlar va tugagan superpowers docs tozalash  

### P3 — scale / ixtiyoriy

16. Postgres migratsiya rejasi  
17. Thumbnail prewarm  
18. Lead form captcha (faqat abuse bo‘lsa)  
19. Admin 2FA (tashqi yoki package)  

---

## 9. Risk matritsasi

| ID | Soha | Jiddiylik | Ehtimol | Effort | |
|----|------|-----------|---------|--------|--|
| SEC-1 CSP | Security | O‘rta | O‘rta | O‘rta | |
| SEC-2 rich HTML | Security | O‘rta | Past* | O‘rta | *staff compromise |
| SEC-3 CSRF-exempt | Security | Past | O‘rta | O‘rta | |
| PERF-1 landing queries | Perf | O‘rta | O‘rta | Past | |
| PERF-2 VisitLog write | Perf | O‘rta | Past→O‘rta | O‘rta | traffic ga bog‘liq |
| UX-1 modal a11y | UX | O‘rta | Yuqori | Past | |
| UX-5 phone mask | UX/Conv | O‘rta | Yuqori | Past | |
| UX-6 fake tel | UX | Past | O‘rta | Juda past | |
| OE dead deps/fields | Maintain | Past | — | Past | |

\*Staff akkaunt buzilsa yuqori.

---

## 10. Test va sifat holati

- Testlar: ~3.3k LOC — deploy hardening, axes lockout, lead rate-limit, map sanitize, translation, certificates va h.k.
- `manage.py check --deploy` production env da toza (test qilingan)
- Eslatma: bu audit **avtomatik Lighthouse / OWASP ZAP / real load test** o‘tkazmagan. Production URL bo‘lsa keyingi qadam sifatida tavsiya etiladi.

---

## 11. Xulosa

Hope School **production-ready marketing + admin stack**. Asosiy investitsiya xavfsizlik va ops ga qilingan — bu to‘g‘ri. Endi eng katta qaytish:

1. **Conversion/UX** mayda tuzatishlar (telefon, modal a11y, soxta tel)  
2. **CSP enforce**  
3. **Landing cache** va keraksiz kod/dep tozalash  
4. Traffic oshganda **VisitLog + SQLite** strategiyasi  

Kod bazasi “vibe-coded chaos” emas — ongli cheklovlar va testlar bilan ushlab turilgan. Ponytail kesishlari asosan **generator/scrap/docs** va **o‘qilmaydigan maydonlar** atrofida; runtime yadrosi nisbatan lean.

---

## 12. Fayl indeksi (auditda ko‘rilgan asosiy joylar)

| Joy | Nima uchun |
|-----|------------|
| `config/settings.py` | Security, cache, axes, unfold |
| `config/urls.py` | Admin URL, lead, sitemap |
| `apps/leads/views.py` | Public form, rate-limit |
| `apps/leads/notifications.py` | Telegram |
| `apps/common/utils.py` | IP, phone, video embed |
| `apps/common/translation.py` | MT pipeline |
| `apps/certificates/services.py` | PDF import / SSRF |
| `apps/analytics/middleware.py` | VisitLog |
| `apps/analytics/dashboard.py` | Admin KPIs |
| `apps/siteconfig/models.py` | Config, map sanitize |
| `apps/pages/views.py` | Landing queries |
| `static/js/main.js` | Frontend UX |
| `templates/base.html`, sections | UI |
| `deploy/hopeschool.uz.conf` | nginx security/perf |
| `deploy/gunicorn.conf.py` | Workers |
| `requirements.txt` | Dependencies |

---

*Bu hujjat bir martalik audit snapshot. O‘zgarishlar kiritilgach qayta audit qilish tavsiya etiladi.*
