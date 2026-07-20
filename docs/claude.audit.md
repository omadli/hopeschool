# Hope School — to'liq audit hisoboti

**Sana:** 2026-07-20
**Auditor:** Claude (Opus 4.8, Anthropic)
**Loyiha:** Hope School — Django 5.2 marketing sayti + Unfold admin + analitika/CRM
**Scope:** xavfsizlik, performance, UI/UX + accessibility, usability, over-engineering (ponytail)
**Metod:** kod/template/deploy konfiguratsiya statik tahlili (5 ta parallel review agent bilan; runtime Lighthouse / penetration / load test **emas**). Dead-code da'volari butun repo bo'yicha grep bilan tasdiqlangan.

> Bu `docs/grok.audit.md` dan **mustaqil** ravishda o'tkazildi. Bir nechta topilma bir-birini tasdiqlaydi; bu audit qo'shimcha ravishda grok topmagan bir necha nuqtani ochdi (DNS-rebinding SSRF, thumbnail decode "bo'roni", HTTP/2 yo'qligi, 404/500 sahifasi yo'qligi, galereya dead-end, o'lik `albums` query).

---

## 1. Qisqa xulosa

Hope School — kichik o'quv markazi uchun **ongli ravishda hardening qilingan**, testlar bilan ushlab turilgan loyiha. Xavfsizlik va frontend asoslari (trusted-proxy IP, axes, SSRF scaffolding, WebP `<picture>`, self-hosted fonts, `prefers-reduced-motion` CSS bloki, skip-link) o'rtacha marketing saytdan sezilarli oldinda. "Vibe-coded chaos" emas.

Eng katta qaytishlar 4 ta nuqtada:

| Soha | Holat | Eng muhim nuqta |
|------|-------|-----------------|
| Xavfsizlik | Yaxshi | `DEBUG` default butun hardeningni gate qiladi; rich-text `\|safe` sanitizer yo'q; cert importerda DNS-rebinding |
| Performance | O'rtacha–Yaxshi | Landing har renderda **~230 thumbnail decode** (dimensions cache yo'q); fragment-cache umuman yo'q; HTTP/2 kafolatlanmagan |
| UI/UX / a11y | Yaxshi | Modal/lightbox focus trap yo'q; carousel keyboard pause + reduced-motion yo'q; toast SR ga e'lon qilinmaydi |
| Usability | O'rtacha–Yaxshi | Privacy sahifasi yo'q; 404/500 template yo'q; galereya lightbox/pagination yo'q; o'lik admin maydonlari |
| Over-engineering | O'rtacha | 1 o'lik dep; o'lik map properties; galereya `albums` query; one-off generatorlar |

**Umumiy ball (subyektiv, 10 dan):**

| Soha | Ball |
|------|------|
| Xavfsizlik | **7.5** |
| Performance | **6.5** |
| UI/UX / a11y | **7.0** |
| Usability | **7.0** |
| Kod soddaligi | **7.5** |
| **Umumiy** | **~7.1** |

> Grok umumiy **~7.6** qo'ygan; men biroz pastroq — asosan **PERF-1 (thumbnail decode bo'roni)** va **UI a11y widget gaplari** grok bahosidan og'irroq deb hisoblayman.

---

## 2. Kuchli tomonlar (saqlash kerak)

- **IP-spoofing-resistant client IP** — `apps/common/utils.py:27` XFF ni **o'ngdan** `TRUSTED_PROXY_COUNT` bilan o'qiydi; nginx `$proxy_add_x_forwarded_for` bilan mos. Rate-limit/geo/axes uchun yagona manba.
- **Brute-force**: axes (IP+username, NAT lockout emas) + nginx `hs_login` regex zone (`ADMIN_URL` renameni ham ushlaydi).
- **Admin hardening**: obfuscated `ADMIN_URL`, `is_superuser` readonly + formdan olib tashlangan, o'zaro superuser himoyasi (`apps/common/admin.py:55`).
- **Injection-safe integratsiyalar**: Telegram xabarlarida har maydon `html.escape`; analytics ID lar strict-regex; map embed nh3 + host allowlist.
- **Cert importer**: har redirect hopni re-validate, 10MB stream cap, non-public IP rad (`services.py`). (SSRF-3 dagi rebinding gapdan tashqari mustahkam.)
- **Image pipeline**: WebP `<picture>` + `width/height` (CLS yo'q) + lazy/eager + hero `fetchpriority=high`. Darslik LCP setup.
- **Fonts**: self-hosted woff2, preload, `font-display:swap`, `unicode-range` subset. Render-blocking Google Fonts yo'q.
- **a11y asoslari**: skip-link → `<main tabindex=-1>`, `focus-visible` (light+dark), honeypot `aria-hidden`, semantik `dl/dt/dd` va `figure/blockquote`, `<button>` cert kartalar, `prefers-reduced-motion` CSS bloki.
- **Static**: `CompressedManifestStaticFilesStorage` + nginx `expires 1y immutable` + `gzip_static`.
- **SQLite tuning**: WAL + `synchronous=NORMAL` + `busy_timeout` + `IMMEDIATE` — kam-write marketing sayt uchun to'g'ri.
- **Solo singletonlar** dedicated LocMemCache da (DB round-trip yo'q).

---

## 3. Xavfsizlik (Security)

### [SEC-1] `DEBUG`/`ALLOWED_HOSTS` default butun hardeningni gate qiladi — **O'rta**

`config/settings.py:19` `DEBUG=(bool, True)`, `:20` `ALLOWED_HOSTS=(list, ["*"])`. `:54` `if not DEBUG:` bloki **hamma narsani** o'raydi: secure/HttpOnly/SameSite cookie, HSTS, SSL redirect, nosniff — **va** yaroqsiz `SECRET_KEY`/`ALLOWED_HOSTS` ni rad qiluvchi fail-fast guardlar ham (`:55`).

**Risk:** production `.env` da bitta `DEBUG` qatori yo'qolsa yoki xato yozilsa → `DEBUG=True` bo'lib qoladi. Uni ushlashi kerak bo'lgan guardlar ayni **shu** blok ichida yashaydi, shuning uchun ular hech qachon ishga tushmaydi. Bitta o'tkazib yuborilgan env → verbose exception (source/settings/secret leak), `ALLOWED_HOSTS=['*']`, HSTS yo'q, HTTP orqali HttpOnly'siz cookie. Bu — butun posturani bir zumda o'chiruvchi tizimli kuchaytirgich.

**Tavsiya:** `DEBUG=(bool, False)`, `ALLOWED_HOSTS=(list, [])` default qiling — dev **opt-in** bo'lsin. SECRET_KEY/ALLOWED_HOSTS sanity check larni `if not DEBUG` dan tashqariga chiqaring.

### [SEC-2] Stored XSS: CKEditor rich-text `|safe`, server-side sanitizer yo'q — **O'rta**

`templates/teachers/detail.html:46`, `courses/detail.html:58`, `news/detail.html:52`, `sections/_about.html:9` — hammasi `CKEditor5Field` ni `|safe` bilan render qiladi. Repo bo'yicha `nh3|bleach|sanitiz` grep — sanitizatsiya **faqat** `siteconfig/models.py` da (map embed). Rich text xom saqlanadi va xom chiqadi. `mediaEmbed.previewsInData=True` (`settings.py:358`) xom `<iframe>` ni ataylab saqlaydi.

**Risk:** teachers/courses/news/pages ni tahrirlash huquqi bor har qanday staff (faqat superuser emas — superuser editorlarga `is_staff` bera oladi) `<script>`/`<img onerror=…>` saqlashi mumkin → **har bir public tashrifchida** bajariladi (persistent XSS, session/credential o'g'irlash, defacement). CSP backstop yo'q (SEC-4).

**Tavsiya:** CKEditor HTML ni output (yoki save) da nh3 allowlist orqali o'tkazing — loyihada aynan shu pattern `sanitize_map_embed` da bor. `render_rich` filter yozing (xavfsiz teg/attr allowlist + kerakli embed iframe larni host bo'yicha ruxsat) va 4 ta `|safe` ni almashtiring.

### [SEC-3] Cert importer: DNS-rebinding orqali blind SSRF (validate→refetch TOCTOU) — **O'rta**

`apps/certificates/services.py:93` `_validate_public_url(current)` hostni `getaddrinfo` bilan resolve qilib har IP public ekanini tekshiradi, keyin `:95` `requests.get(current, …)` **mustaqil ikkinchi** DNS resolve qiladi. Tekshirilgan IP va ulanadigan IP bir xil bo'lishi kafolatlanmagan.

**Risk:** attacker-controlled domen (admin skanerlaydigan cert **QR kod** yoki `external_url` orqali) validation lookupga public IP, fetch lookupga `169.254.169.254`/`127.0.0.1` javob berishi mumkin (DNS rebinding). `%PDF-`/Content-Type gate exfiltratsiyani qiyinlashtiradi → bu **blind** SSRF (timing/error oracle) internal xizmatlarga. Admin-triggered, lekin URL tashqaridan keladi.

**Tavsiya:** hostni **bir marta** resolve qiling, tasdiqlangan public IP ni tanlang va o'sha IP ga ulaning (address pinning), original `Host` header saqlab. Mavjud per-redirect re-validation qolsin.

### [SEC-4] Content-Security-Policy amalda yo'q — **Past–O'rta**

`deploy/hopeschool.uz.conf:63` — CSP butunlay kommentariyada; hatto staged rollout ham faqat `Report-Only`. Aktiv `add_header` ham, Django-side CSP ham yo'q. Fayl CI/CD orqali auto-deploy ham qilinmaydi.

**Risk:** CSP yo'qligida SEC-2 (va har qanday reflected/DOM XSS) cheklovsiz bajariladi — `script-src` allowlist yo'q, `frame-ancestors` yo'q. Qoralama yaxshi, faqat yoqilmagan.

**Tavsiya:** hujjatlangan rolloutni yakunlang (Report-Only → enforce) va serverga qo'ying. SEC-2 tuzatilgunga qadar ikkilamchi himoya yo'q.

### [SEC-5] To'liq sertifikat rasmlari public (o'quvchi PII) — **O'rta (privacy)**

`CertificateListView` har `is_active` uchun `Certificate.image` ni chiqaradi; rasm — CEFR PDF ning **birinchi to'liq sahifasi** (`services.py:140`), `student_name` saqlanadi/ko'rsatiladi. Media public + 30-kun public cache.

**Risk:** CEFR skanlarida odatda to'liq ism, sertifikat seriyasi, sana, ba'zan ID/foto bo'ladi — bu yerda maktab o'quvchilari (ehtimol voyaga yetmaganlar). To'liq rasmni public qilish shu PD ni world-readable + cacheable qiladi. (Bu jamoaning o'z ochiq savoli — "cert PII redaction" bilan mos.)

**Tavsiya:** ongli qaror: rendered rasmni non-identifying badge zonasigacha crop/redact; yoki full rasmni auth ortiga; yoki faqat level + ism ko'rsatish. Minimal: `student_name` to'liq va seriyani public outputdan olib tashlash.

### [SEC-6] `/ariza/` CSRF-exempt; Origin yo'q bo'lsa o'tadi — **Past (mitigatsiyalangan)**

`apps/leads/views.py:58` `@csrf_exempt`; `_origin_allowed` (`:20`) `HTTP_ORIGIN` yo'q bo'lsa `True` qaytaradi.

**Risk:** Origin yubormaydigan clientdan cross-site majburiy submit. Realistik past: brauzerlar cross-origin POST da Origin yuboradi (mismatch → 403), yana honeypot + per-IP rate-limit + nginx `hs_form`. Xavf ostidagi yagona narsa — spam lead qatorlari (allaqachon flood-control). Hujjatlangan tradeoff (stale-token 403) asosli.

**Tavsiya:** as-is qabul qilsa bo'ladi. Qoldiq gapni yopish uchun: Origin **ham** yo'q, allowed-host Referer **ham** yo'q POST larni rad qiling (absence da ruxsat berish o'rniga).

### 3.1. Tekshirildi — muammo EMAS (bo'ri qichqirmaslik)

- `video.video_embed` → `<iframe src>`: manba `URLField` (`URLValidator` `javascript:`/`data:` ni rad qiladi). Attribute konteksti autoescaped. Exploit emas.
- `latitude`/`longitude` unvalidated `CharField` lekin har sink autoescaped yoki `|escapejs` — eng yomoni buzilgan URL, XSS emas.
- GA4/verification ID lar inline JS/meta da: regex-locked / autoescaped attribute. Breakout yo'q.
- Lead rate-limit: shared `DatabaseCache`, faqat accepted save sanaladi — to'g'ri, per-process emas.

---

## 4. Performance

### Landing render budjeti (to'liq to'ldirilgan DB, kod tahlilidan taxmin)

| Manba | Narx |
|-------|------|
| `LandingView.get_context_data` | ~11 model query |
| `site_context` processor | 3 solo (LocMem, DB yo'q) + 2 DatabaseCache o'qish |
| **easy-thumbnails dimension o'qish** | **~230 DB SELECT + ~230 PIL open/decode + ~460 `os.stat`** |
| Page/fragment cache | **yo'q** — hammasi har anonim hitda ishlaydi |

Thumbnail ishi qolganini **kattalik tartibida** ustun bosadi.

### [PERF-1] easy-thumbnails har renderda har thumbnailni qayta ochib decode qiladi — **Yuqori**

`apps/common/templatetags/media_tags.py:80` har generated thumbnailda `.width/.height` o'qiydi. Cache hitda ham `.width` → `_get_image_dimensions` → `self.open()` (shartsiz) → `THUMBNAIL_CACHE_DIMENSIONS` **o'rnatilmagan** (default `False`, `settings.py` da yo'q) → PIL `get_image_dimensions()` decode, va **saqlanmaydi**, shuning uchun cheksiz takrorlanadi.

**Impact:** har `{% responsive_img %}` 4 tagacha thumbnail (base, 2x, webp, webp 2x). Landingda ~57 rasm → **~230 thumbnail × (1 SELECT + 1 open + 1 decode)** har renderda. Shared VPS da har landing hitiga o'nlab–yuzlab ms CPU+I/O.

**Tavsiya (ikkalasini ham):**
1. `THUMBNAIL_CACHE_DIMENSIONS = True` → birinchi renderdan keyin dimensions SELECT ichida qaytadi, **PIL decode yo'qoladi** (dominant CPU). SELECT/open ni olib tashlamaydi.
2. Image-og'ir bo'limlarni fragment-cache (PERF-2) → SELECT va open ham yo'qoladi.

**Tekshirish (maintainer, populated DB):**
```python
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.test import Client
with CaptureQueriesContext(connection) as ctx:
    Client().get("/")
print(len(ctx))
```

### [PERF-2] Landingda server-side cache umuman yo'q — **Yuqori**

`settings.py:142` MIDDLEWARE da `CacheMiddleware` yo'q; `apps/pages/views.py` oddiy `TemplateView`; `templates/` bo'yicha `{% cache %}` grep — **hech narsa**. Har anonim tashrifchi to'liq ~11 query + ~230 thumbnail + to'liq render ishga tushiradi. Kontent kamdan-kam o'zgaradi.

**Tavsiya:** faqat **image-og'ir, statik** bo'limlarni `LANGUAGE_CODE` bo'yicha `{% cache %}` ga o'rang:
```django
{% load cache %}
{% cache 600 landing_teachers LANGUAGE_CODE %}{% include "sections/_teachers.html" %}{% endcache %}
```
Hero, partners, about, courses, news, teachers, results, gallery, video ga qo'llang.

> ⚠️ **KRITIK caveat (e'tiborsiz qolsa saytni buzadi):** `sections/_contact.html` ni cache QILMANG — unda `{% csrf_token %}` bor (`_contact.html:17`); shared fragment bitta tashrifchi tokenini hammaga beradi va har submitni buzadi. Kontakt bo'limi cache'siz qolsin. Theme (dark/light) client-side CSS — cache-keyga kerak emas, faqat tilga key qiling. Invalidatsiya: `post_save` signal yoki qisqa TTL.

### [PERF-3] Cold thumbnail generatsiyasi 60s timeout ostida sync worker'ni bloklaydi — **O'rta**

Thumbnaillar **birinchi so'rovda** generate qilinadi, `collectstatic` da emas. `deploy/gunicorn.conf.py` = 3 **sync** worker, `timeout=60`.

**Impact:** deploydan yoki yangi kontent yuklamdan keyin birinchi hit ~230 thumbnailni (Pillow resize + WebP encode) sync generate qiladi → realistik 502 va worker band bo'lishi.

**Tavsiya:** deployga warm-up qadam qo'shing (landingni bir marta render qiladigan `manage.py` komandasi). Birinchi real tashrifchi generatsiya narxini to'lamaydi.

### [PERF-4] Landing querysetlari render bo'lmaydigan to'liq body/description tortadi — **O'rta**

`apps/pages/views.py:23` — `courses[:9]`, `news[:8]`, `teachers[:12]`, `certificates[:12]`, `testimonials[:12]` **barcha** ustunni tortadi. `modeltranslation` bilan har CKEditor/text maydon ×3 (`_uz/_ru/_en`). Landing kartalar faqat title/excerpt/image render qiladi, to'liq `body` emas.

**Tavsiya:** landing querysetlarga `.defer("body_uz","body_ru","body_en", ...)` (yoki `.only(...)`). Detail sahifalar to'liq qoladi.

### [PERF-5] Analytics: har public GET da sync SQLite write + UA parse — **O'rta**

`apps/analytics/middleware.py:42` — response'dan keyin `user_agents.parse()` (regex-og'ir) + sync `VisitLog.objects.create()`. SQLite `IMMEDIATE` (har write yagona writer lockni darrov oladi).

**Impact:** request pathga write-locked INSERT qo'shiladi; 3 worker bo'ylab serialize (busy_timeout=5000 bilan chegaralangan). Kam trafik uchun OK; burst da bottleneck. `try/except` breakage'ni to'sadi, latency'ni emas.

**Tavsiya:** hozirgi scale uchun as-is qabul qilsa bo'ladi (WAL yumshatadi). Trafik oshsa writeni request pathdan chiqaring (buffer + flush). Bot/static/admin/staff filtri allaqachon bor — yaxshi.

### [PERF-6] HTTP/2 TLS blokida kafolatlanmagan — **O'rta**

`deploy/hopeschool.uz.conf:22` faqat `:80` serverni belgilaydi; `:443` blokni certbot generatsiya qiladi va odatda `http2 on;` qo'shmaydi. Sahifa **60+ rasm** so'raydi (barcha thumbnail variantlari).

**Impact:** HTTP/2 multiplexing yo'q → 60+ rasm so'rovi HTTP/1.1 head-of-line blocking → aynan shu image-zich landingda sezilarli sekin LCP/load.

**Tavsiya:** certbotdan keyin TLS blokda `http2 on;` (nginx ≥1.25) borligini tekshiring. Bir qator; katta yutuq. (Fayl CI/CD auto-deploy emas — qo'lda qo'llash kerak.)

### [PERF-7] Ikki map iframe ham DOM ga render — **Past**

`templates/sections/_contact.html:47` Google va Yandex `<iframe>` ni render qiladi, ikkinchisi `hidden`. Ikkalasi `loading="lazy"`. `display:none` + below-fold → real narx odatda ~nol, lekin hidden frame src commit qilingan. **Tavsiya (ixtiyoriy):** hidden frame `src` ni faqat tab bosilganda quring (`data-src`→`src`).

### [PERF-8] Scroll handler har frame shartsiz style yozadi — **Past**

`static/js/main.js:9` `onScroll` har scrollda `#hdr` ga 6 inline style yozadi (holat o'zgardimi yo'qmi). `{passive:true}` + rAF guard yumshatadi. **Tavsiya:** `scrolled` bool state, faqat transitionda style tegish.

### 4.1. Kuzatuvlar
- nginx `/static/` ni to'g'ridan serve qiladi → WhiteNoise middleware prod'da amalda o'lik yuk (zararsiz).
- `context_processors.py` social_links/lead_courses ni `DatabaseCache` da saqlaydi — model query'ni cache-table query'ga almashtiradi (kichikroq query, olib tashlangan DB hit emas; in-code izoh biroz ortiqcha maqtaydi).
- Query gigiyenasi yaxshi: `select_related("category")`, `select_related("album")`, `.only("id","name")`. Section templatelarda FK N+1 yo'q.

---

## 5. UI / UX + Accessibility

> a11y-aware kod bazasi: skip-link, `focus-visible` (light+dark), `prefers-reduced-motion` CSS bloki, honeypot `aria-hidden`, semantik `dl/dt/dd` va `figure/blockquote`, `<button>` cert kartalar. Gaplar **JS-driven widgetlarda** to'plangan (modal, dropdown, drawer, carousel, lightbox, toast) — vizual toggle bor, ARIA-state/focus management yo'q.

### [UX-1] Modal + cert lightbox: focus trap, focus move-in, focus restore, dialog role yo'q — **Yuqori (a11y)**

`partials/_modal.html:2`, `partials/_certificate_lightbox.html:3`, `main.js:136`. `openM()`/`openCertLb()` faqat `hidden` klassni olib tashlaydi + scroll lock. Focus dialogga o'tmaydi, Tab ichida qamalmaydi (orqadagi header/nav/footer'ga chiqadi), yopilganda triggerga qaytmaydi. `role="dialog"`/`aria-modal`/`aria-labelledby` yo'q.

**Tavsiya:** ochilganda `document.activeElement` saqlash, panelga `role="dialog" aria-modal="true" aria-labelledby`, birinchi focusable'ga focus, Tab trap (first↔last wrap); yopilganda triggerga restore. Bitta shared helper ikkalasiga xizmat qiladi (logika duplicate).

### [UX-2] Autoplay carousel/ticker: keyboard pause yo'q, reduced-motion e'tiborsiz (WCAG 2.2.2) — **Yuqori**

`main.js:83` carousellar `setInterval` bilan auto-advance, faqat `mouseenter`/`touchstart` da pause — **keyboard focusda emas**. Ticker (`:106`) har 4s aylanadi, pause umuman yo'q. JS motion `prefers-reduced-motion` ni tekshirmaydi (CSS blok `setInterval`+`scrollTo` ni to'xtata olmaydi).

**Tavsiya:** autoplayni `matchMedia('(prefers-reduced-motion: reduce)').matches` da o'chiring; `focusin`→stop / `focusout`→start qo'shing; ticker uchun ham reduced-motion guard; ko'rinadigan pause tugmasi.

### [UX-3] Mobile call tugmasida hardcoded soxta telefon — **O'rta**

`partials/_mobile_bar.html:3` `tel:{{ ...|default:'+998901234567' }}`. Footer/contact `{% if phone_primary %}` bilan himoyalangan; doim-ko'rinadigan mobile tugma esa config bo'sh bo'lsa **soxta raqamga** qo'ng'iroq qiladi (ishlagandek ko'rinadi — o'lik havoladan yomonroq).

**Tavsiya:** footer kabi guard qiling; yoki fallbackni modal/contact anchorga yo'naltiring.

### [UX-4] Interaktiv toggle'lar `aria-expanded` yangilamaydi — **O'rta**

Til dropdown (`_header.html:21` + `main.js:47`): `aria-haspopup` bor, `aria-expanded` yo'q va JS o'rnatmaydi. Burger (`aria-controls="drawer"`, expanded yo'q). Modal trigger'lar (`_hero.html:18` va h.k.): `aria-haspopup="dialog"` ham, `aria-expanded` ham yo'q.

**Tavsiya:** har handlerda `setAttribute('aria-expanded', String(!hidden))`; markupda `aria-expanded="false"` init; modal trigger'larga `aria-haspopup="dialog"`.

### [UX-5] Success toast SR ga e'lon qilinmaydi — **O'rta**

`base.html:53` `#toast` — oddiy `<div>`, `role="status"`/`aria-live` yo'q. Submit muvaffaqiyati **faqat vizual**. Ko'r foydalanuvchi lead yuboradi, toast 3.2s chaqnab yo'qoladi, tasdiq olmaydi — lead-gen saytda conversion-kritik moment.

**Tavsiya:** wrapper'ga `role="status"`. `hidden` (display:none) bo'lgani uchun successda focus ko'chirishni ham ko'ring.

### [UX-6] Form xatolari maydonga bog'lanmagan; `aria-invalid` yo'q — **O'rta**

`main.js:188` per-field xatolarni bitta shared `[data-form-error]` ga yig'adi. `aria-invalid` yo'q, `aria-describedby` yo'q, birinchi xato maydonga focus yo'q. Qaysi maydon xato — ma'lum emas.
> Yana: xato box'iga `role="alert"` **va** `aria-live="polite"` berilgan — `alert` implicit *assertive*, ikkisi ziddiyatli; faqat `role="alert"` qoldiring.

**Tavsiya:** `d.errors` maydon nomlaganda o'sha input'larga `aria-invalid="true"` + `aria-describedby`, xabarni maydon yonida render, birinchisiga `.focus()`.

### [UX-7] Modal form placeholder-as-label ishlatadi — **O'rta**

`_modal.html:16` — faqat `aria-label`+`placeholder`, ko'rinadigan `<label>` yo'q. (Kontakt form `_contact.html:21` **to'g'ri** `<label for>` ishlatadi — nusxa oling.) Placeholder yozilganda yo'qoladi + low-contrast gray.

### [UX-8] Drawer/til dropdown Escape bilan yopilmaydi; focus management yo'q — **O'rta**

Escape modal+lightboxni yopadi (yaxshi), lekin drawer/til menyusi uchun yo'q; drawer ochilganda focus ichiga o'tmaydi/qamalmaydi. **Tavsiya:** ikkalasiga Escape-close; drawer ochilganda birinchi linkga focus, yopilganda burgerga restore.

### 5.1. Past severity (qisqa)
- **[UX-9]** Dark-mode toggle `aria-pressed` yo'q (`_header.html:34`).
- **[UX-10]** Count-up (`main.js:72`) reduced-motion e'tiborsiz — set qiymatni darrov.
- **[UX-11]** JS smooth-scroll (`main.js:89,249`) reduced-motion CSS ni bypass qiladi.
- **[UX-12]** Partners marquee dublikat `aria-hidden` emas (AT ikki marta o'qiydi); footer `<h3>` `<h2>` siz — heading skip.
- **[UX-13]** Kichik ikon tap-target: footer h-9 (36px), contact/teachers h-8 (32px) — AA 24px o'tadi, lekin 44px dan past.
- **[UX-14]** Dekorativ inline SVG lar nomuvofiq belgilangan (ba'zi `aria-hidden` bor, ko'pi yo'q).
- **[UX-15]** Submit tugmasi "sending" holatini ko'rsatmaydi (faqat `disabled`).
- **[UX-16]** Aktiv til/joriy sahifa `aria-current` yo'q (faqat rang).

> **Kontrast** umuman AA o'tadi (`--soft` #566076 ~6.3:1, brand-blue-600 ~6.8:1). Yagona caveat — placeholder-as-label (UX-7).

---

## 6. Usability

### 6.1. Public sayt

- **[USE-1] PII yig'ilayotganda privacy/oferta/terms sahifasi yo'q — Yuqori.** Grep `privacy|terms|oferta|maxfiylik|shartlar` → nol user-facing sahifa. Lead ism+telefon oladi va Telegramga uzatadi. Footerda faqat copyright. **Tavsiya:** minimal privacy/oferta template + `_footer.html` va lead form yonida havola.
- **[USE-2] Custom 404/500 template yo'q — O'rta.** `templates/404.html`/`500.html` yo'q, `handler404/500` yo'q. `DEBUG=False` da production stillashmagan matn sahifa beradi — brand yo'qotish, convert yo'li yo'q. **Tavsiya:** `base.html` ni extend qilgan 404/500 + home link + lead CTA.
- **[USE-3] Galereya browse dead-end: lightbox yo'q, pagination yo'q — O'rta.** `gallery/list.html:37` har fotoni interaktiv bo'lmagan `<div>` ga qo'yadi (sertifikatlar `data-cert-open` bilan ochiladi). `gallery/views.py` oddiy `TemplateView`, `paginate_by` yo'q — barcha aktiv rasm+video bitta sahifada. **Tavsiya:** mavjud cert lightboxni galereyaga qayta ishlating; grid paginate.
- **[USE-4] Lead-source scheme JS-bog'liq va mo'rt — O'rta.** Reklama linklari `.../#contact?source=telegram` — `?source=` URL **fragment** ichida, serverga hech qachon yuborilmaydi; client-side parse qilinadi (`main.js:234`). JS o'chirilgan bo'lsa `source` jimgina `site` ga tushadi → pullik leadlar noto'g'ri attribute. Alohida: standart `utm_source` boshqa maydonga (`referrer`) tushadi — ikkita ustma-ust source tushunchasi. **Tavsiya:** haqiqiy query param ishlating (`/{lang}/?source=telegram#contact`) — server to'g'ridan o'qiydi, JS-off da ham saqlanadi.
- **[USE-5] Generic JS error toast hardcoded o'zbekcha — Past.** `main.js:208` `GENERIC = "Xatolik yuz berdi…"` — ru/en tashrifchi network xatoda o'zbekcha ko'radi (server xabarlari tarjimalangan). **Tavsiya:** translated `data-` attribute orqali.
- **[USE-6] Telefon maydonida client-side mask/inputmode yo'q — Past.** `+998`+12 raqam qoidasi faqat server round-tripdan keyin. **Tavsiya:** `inputmode="tel"` + yengil prefix mask.

*(Til almashtirish, tel: linklar, homepage empty-state guardlar (`{% if courses %}`), cert pagination/lightbox — tekshirildi, to'g'ri.)*

### 6.2. Admin (operator)

- **[USE-7] O'lik admin config: Yandex map override + chalkash dual map config — O'rta.** Admin `google_maps_embed` **va** `yandex_maps_embed` override + lat/lng koordinata ko'rsatadi. Lekin contact template faqat `safe_google_maps_embed` yoki koord-based iframe render qiladi — `yandex_maps_embed`/`safe_yandex_maps_embed` **hech qayerda render qilinmaydi** (grep-tasdiq, nol reader). Operator Yandex to'ldirsa — effekt yo'q. **Tavsiya:** `yandex_maps_embed` maydon+property'ni o'chiring; koord birlamchi ekanini relabel qiling.
- **[USE-8] News & Testimonials da `is_featured` saytda hech narsa qilmaydi — O'rta.** Ikkala model `is_featured` ni `list_display/list_editable/list_filter` da ko'rsatadi, lekin view/template hech biri query/render qilmaydi (grep-tasdiq, nol reader). News default order, Testimonials faqat `is_active` filtrlaydi. (Eslatma: `courses.is_featured` **jonli** — `_courses.html:17` qizil badge.) **Tavsiya:** featured itemlarni tepaga chiqaring yoki toggle'ni o'chiring.
- **[USE-9] Landing kontent modeli juda fragmentlangan — Past.** `pages` app bitta landing uchun 6 alohida admin surface (HeroSection, HomeVideo, AboutSection, StatItem, WhyUsItem, SiteCopy) + `SiteConfig`. Har bo'lim bo'sh bo'lsa o'zini yashiradi → yangi seeded sayt deyarli bo'sh landing beradi. **Tavsiya:** kod o'zgarishi shart emas; `docs/ADMIN.md` ga content-onboarding checklist go-live'ni de-risk qiladi.

*(Dual Telegram config — panel token vs `.env` — aslida toza ishlangan: write-only password, read-only status, `.env` fallback. Defekt emas.)*

---

## 7. Over-engineering audit (ponytail)

> Har dead-code da'vosi butun repo grep bilan tasdiqlangan.

- **[OE-1] `django-import-export` — nol usage · O'rta impact, trivial effort.** Grep `import_export|ImportExport|ExportMixin|resources\.` → **nol hit**; `INSTALLED_APPS` da yo'q. `requirements.txt` + `constraints.txt` da e'lon qilingan. **Aksiya:** ikkala qatorni o'chiring (`tablib`/`diff-match-patch` transitive og'irlik ham ketadi).
- **[OE-2] `SiteConfig` da o'lik map helper properties · Past, trivial.** Grep (butun repo): `google_maps_link`, `yandex_maps_link`, `safe_yandex_maps_embed`, `yandex_map_src` — **nol reader**. `google_map_src` property faqat `siteconfig/tests.py:61` da (template'lar lang-aware `ui.py` tagini ishlatadi — property redundant). `models.py:159-184` (~26 qator). **Aksiya:** to'rt o'lik property + redundant `google_map_src` ni o'chiring (testni drop/rewrite).
- **[OE-3] Galereya `albums` o'lik query har page loadda · Past.** `gallery/views.py:11` `ctx["albums"]` ni `prefetch_related("images")` bilan quradi, lekin `gallery/list.html` `albums` ga hech qachon murojaat qilmaydi (grep → nol hit). Har requestga behuda query+prefetch. **Aksiya:** `albums` qatorini o'chiring (yoki album browsing'ni tugating).
- **[OE-4] One-off locale generator skriptlari · Past.** `locale/_gen_translations.py` (o'zi "One-off… Not imported anywhere"), `_make_extra.py`, `_verify.py`, `_draft_translations.txt` — chiqishi `_extra_translations.py` da. Runtime faqat `.mo` (CI `compilemo`). **Aksiya:** 4 ta spent artifactni o'chiring (git history saqlaydi). `_build_catalogs.py`/`_build_uz_admin.py` qolsin.
- **[OE-5] `scripts/_fetch_fonts.py` spent one-off · Past.** Yuklaydigan fontlar allaqachon vendored + `_fonts.html` da referenced. **Aksiya:** o'chiring.
- **[OE-6] `docs/superpowers/*` — ship bo'lgan feature reja/spec · Past.** 7 plan+spec (crm-lead-source, dashboard-filter, partners, mobile-pwa) — hammasi jonli kodda. **Aksiya:** archive/delete; living doc emas.
- **[OE-7] Deyarli bir xil sitemap klasslar · Trivial.** `common/sitemaps.py` — `Course/Teacher/News` faqat `items()`/`changefreq`/`priority` da farq; ~15 qator i18n/alternates boilerplate duplicate. **Aksiya:** bitta parametrlangan base'ga yig'ing (faqat shu faylga tegilsa).

### 7.1. O'chirilmasin (asosli murakkablik)

| Qism | Sabab |
|------|--------|
| `apps/common/translation.py` | Haqiqiy admin MT feature |
| `certificates/services.py` | SSRF-aware PDF import |
| Analytics middleware + dashboard | Operatorga in-panel dashboard beradi (GA ID lar bermaydi) — ongli build-vs-buy |
| `OrderedActiveModel` / `VideoMixin` | Ko'p modelda |
| axes, nh3, polib, solo, pypdfium2 | Aniq vazifa |
| Testlar | Coverage, bloat emas |

> `_scratch/` (posts.json 106KB + fetch_hope.py) va `cefr_urls.txt` — **gitignored**, repo bloat emas (grokdan farq: ular repoda emas). Lokal qulay bo'lганда o'chiring.

---

## 8. Prioritetli harakatlar rejasi

### P0 — tez / yuqori foyda (1–2 kun)
1. **[SEC-1]** `DEBUG`/`ALLOWED_HOSTS` defaultini flip qiling (dev opt-in)
2. **[PERF-1]** `THUMBNAIL_CACHE_DIMENSIONS = True` (bir qator, decode bo'ronini o'ldiradi)
3. **[UX-3]/[USE-7]** Mobile bar soxta `tel:` ni guard qiling
4. **[OE-1]** `django-import-export` ni requirements/constraints dan o'chiring
5. **[OE-3]** Galereya `albums` o'lik queryni o'chiring
6. **[USE-2]** 404/500 template

### P1 — muhim (1 hafta)
7. **[PERF-2]** Landing bo'limlarni fragment-cache (kontakt'dan tashqari — CSRF caveat!)
8. **[SEC-2]** Rich-text public sanitize (nh3 allowlist, mavjud pattern)
9. **[UX-1]** Modal + lightbox focus trap/restore (shared helper)
10. **[UX-2]** Carousel/ticker: reduced-motion + keyboard pause
11. **[USE-1]** Privacy/oferta sahifasi
12. **[SEC-4]** CSP Report-Only → enforce
13. **[PERF-6]** TLS blokda `http2 on;` (bir qator)

### P2 — o'rta muddat
14. **[SEC-3]** Cert importer DNS-rebinding: address pinning
15. **[PERF-3]** Deploy thumbnail warm-up
16. **[PERF-4]** Landing querysetlarga `.defer(body_*)`
17. **[UX-4/5/6/8]** ARIA-state, toast `role=status`, form error binding, drawer Escape
18. **[USE-3]** Galereya lightbox + pagination
19. **[USE-4]** Lead-source query param (fragment emas)
20. **[USE-7/8]/[OE-2]** O'lik map/`is_featured` maydonlarni o'chiring yoki wire qiling

### P3 — scale / ixtiyoriy
21. **[PERF-5]** VisitLog writeni request pathdan chiqarish (trafik oshsa)
22. **[SEC-5]** Cert PII redaction qarori
23. Postgres migratsiya rejasi (SQLite ceiling)
24. **[OE-4/5/6/7]** locale one-off, superpowers docs, sitemap dedup tozalash

---

## 9. Risk matritsasi

| ID | Soha | Jiddiylik | Ehtimol | Effort |
|----|------|-----------|---------|--------|
| SEC-1 DEBUG gate | Security | O'rta | Past* | Juda past |
| SEC-2 rich HTML XSS | Security | O'rta | Past** | O'rta |
| SEC-3 DNS-rebind SSRF | Security | O'rta | Past | O'rta |
| SEC-5 cert PII | Privacy | O'rta | Yuqori | O'rta |
| PERF-1 thumbnail decode | Perf | Yuqori | Yuqori | Juda past |
| PERF-2 no fragment cache | Perf | Yuqori | Yuqori | Past |
| PERF-6 no HTTP/2 | Perf | O'rta | O'rta | Juda past |
| UX-1 modal focus trap | UX/a11y | O'rta | Yuqori | Past |
| UX-2 carousel a11y | UX/a11y | O'rta | Yuqori | Past |
| USE-1 no privacy page | Legal/UX | O'rta | Yuqori | Past |
| USE-2 no 404/500 | UX | Past | O'rta | Juda past |
| OE dead deps/fields | Maintain | Past | — | Past |

\* Bir env qatoriga bog'liq — sodir bo'lsa jiddiyligi yuqori.
\*\* Staff akkaunt buzilsa yoki editor yollansa yuqori.

---

## 10. Grok auditidan farqlar (qo'shilgan qiymat)

Bu audit grok bilan ko'p nuqtada mos (CSP, CSRF-exempt, VisitLog, modal a11y, reduced-motion, o'lik maydonlar, import-export). Grok topmagan yoki men aniqroq qildim:

- **PERF-1 — thumbnail decode bo'roni (~230 op/render).** Grok buni "Past–O'rta first-hit cost" deb baholagan; aslida **har render**da takrorlanadi (`THUMBNAIL_CACHE_DIMENSIONS` yo'q) — Yuqori.
- **PERF-2 — fragment cache umuman yo'q + kontaktdagi CSRF caveat.** Grok "cache to yig'ish" tavsiya qilgan, lekin CSRF token bilan shared fragment saytni buzishini aytmagan.
- **PERF-6 — HTTP/2 kafolatlanmagan** (60+ rasmli sahifada katta).
- **SEC-3 — DNS-rebinding TOCTOU** cert importerda (grok umumiy "SSRF guard yaxshi" degan).
- **SEC-1 — DEBUG default butun blokni gate qilishi** (grok "Past" degan; tizimli amplifier sifatida kuchliroq).
- **USE-2 — 404/500 template yo'q**, **USE-3 — galereya dead-end**, **OE-3 — o'lik `albums` query**, **UX-5 — toast SR e'lon qilinmaydi**, **UX-6 — role=alert+aria-live ziddiyati** — grokda yo'q.

---

## 11. Xulosa

Hope School **production-ready**. Asosiy investitsiya xavfsizlik + ops ga qilingan va bu to'g'ri. Eng katta qaytishlar tartib bilan:

1. **PERF-1 + PERF-2** — bitta setting flag + fragment-cache landing render narxini kattalik tartibida tushiradi (eng arzon, eng katta yutuq).
2. **SEC-1** default flip + **SEC-2** rich-text sanitize — mavjud pattern bilan.
3. **UI a11y widgetlari** (modal focus trap, carousel pause) — foydalanuvchi ta'siri yuqori, effort past.
4. **USE-1/2/3** — privacy sahifasi, 404/500, galereya lightbox — ishonch va conversion.
5. O'lik kod/dep tozalash (OE-1/2/3) — arzon maintain yutug'i.

Ponytail kesishlari **runtime yadrosini** deyarli buzmaydi (asosan o'lik property/query/dep va one-off generatorlar). Kod bazasi ongli cheklovlar bilan ushlab turilgan — audit shuni kuchaytirishga qaratilgan.

---

*Bu hujjat bir martalik audit snapshot (statik tahlil). Runtime Lighthouse / OWASP ZAP / load test keyingi qadam sifatida tavsiya etiladi. O'zgarishlar kiritilgach qayta audit tavsiya etiladi.*
