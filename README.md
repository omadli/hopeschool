# Hope School — Oʻquv Markazi Sayti

> **Bogʻiturkon qishlogʻi (Romitan, Buxoro) uchun zamonaviy taʼlim markazi landing sayti.**
> Toʻliq admin-boshqaruv, 3 til (oʻzbek / rus / ingliz), Node.js talab qilinmaydi.

---

## Mundarija

1. [Loyiha haqida](#loyiha-haqida)
2. [Imkoniyatlar](#imkoniyatlar)
3. [Texnologiyalar](#texnologiyalar)
4. [Talablar](#talablar)
5. [Oʻrnatish](#ornatish)
6. [Muhit oʻzgaruvchilari](#muhit-ozgaruvchilari)
7. [Management buyruqlari](#management-buyruqlari)
8. [Loyiha tuzilishi](#loyiha-tuzilishi)
9. [Arizalar va Telegram](#arizalar-va-telegram)
10. [Tashriflar va Analitika](#tashriflar-va-analitika)
11. [i18n / Tarjima](#i18n--tarjima)
12. [Media xavfsizligi va CKEditor](#media-xavfsizligi-va-ckeditor)
13. [Deployment](#deployment)

---

## Loyiha haqida

**Hope School** — Buxoro viloyati, Romitan tumani, Bogʻiturkon qishlogʻidagi oʻquv markazi uchun yaratilgan reklama/landing veb-sayt. Sayt potentsial oʻquvchilar va ota-onalarga markaz haqida toʻliq maʼlumot beradi va ariza topshirish imkonini yaratadi.

Asosiy xususiyatlar:

- **Reklama maqsadida** — kurslar, oʻqituvchilar, muvaffaqiyatlar, sertifikatlar va ota-onalar fikrlari orqali markazni taqdim etadi.
- **3 til** — oʻzbek (standart), rus va ingliz tillari qoʻllab-quvvatlanadi; har bir kontent admin paneldan alohida kiritiladi.
- **Toʻliq CMS-boshqaruv** — Django Unfold admin paneli orqali texnik bilimisiz barcha kontent, sozlamalar va arizalar boshqariladi.

---

## Imkoniyatlar

| # | Imkoniyat | Holat | Tavsif |
|---|-----------|-------|--------|
| 1 | **Kurslar** | ✓ Tayyor | Toifalar bilan kurslar roʻyxati, har bir kurs uchun batafsil sahifa; narx, guruh hajmi, CKEditor tavsif |
| 2 | **Oʻqituvchilar** | ✓ Tayyor | Profil sahifasi, tajriba yillari, fanlar, ijtimoiy tarmoq havolalari |
| 3 | **Galereya** | ✓ Tayyor | Albomlar tizimi, har bir albomda cheksiz rasm; ALT matn (SEO) |
| 4 | **Yangiliklar va eʼlonlar** | ✓ Tayyor | Maqolalar, badge/tag, muqova rasm, chop etish sanasi, SEO meta |
| 5 | **Sertifikatlar** | ✓ Tayyor | Oʻquvchi yutuqlari — rasm, PDF yoki tashqi havola bilan |
| 6 | **Ota-ona fikrlari** | ✓ Tayyor | Sharh matn, rasm, reyting (1–5), tanlangan belgi |
| 7 | **Statistika bloklari** | ✓ Tayyor | Admin paneldan boshqariladigan raqamlar (oʻquvchilar soni, yoʻnalishlar va h.k.) |
| 8 | **"Nega biz" bloklari** | ✓ Tayyor | Ikonkali afzallik kartalari, admin orqali tartiblanadi |
| 9 | **Ariza formasi + Telegram** | ✓ Tayyor | `/ariza/` → DB → admin "Murojaatlar → Arizalar" + sidebar badge; Telegram bot bildirishnoma; honeypot + IP rate-limit spam himoyasi |
| 10 | **Tashriflar hisobi (Analitika)** | ⟳ Qoʻshilmoqda | VisitLog middleware, KPI dashboard, `prune_visitlogs` buyruq |
| 11 | **SEO tayyorligi** | ✓ Tayyor | Har bir sahifa uchun meta sarlavha/tavsif, OG rasm; Google, Yandex, Bing webmaster tasdiqlash; GA4, Yandex.Metrica; sitemap |
| 12 | **Xaritadan joylashuv tanlash** | ✓ Tayyor | Admin panelda interaktiv Leaflet xarita — belgi bosish yoki manzil qidirish orqali koordinatalar avtomatik toʻladi; Google va Yandex xaritalar shu koordinatalardan quriladi |
| 13 | **Kunduzgi/tungi rejim** | ✓ Tayyor | LocalStorage + `prefers-color-scheme` orqali temir-flash yoʻq mavzu almashish |
| 14 | **CKEditor 5 rich-text** | ✓ Tayyor | Admin kontent maydonlarida formatlash, rasm yuklash |
| 15 | **Media xavfsizligi** | ✓ Tayyor | Rasm: jpg/jpeg/png/webp/gif, maks 5 MB; PDF: 10 MB; CKEditor yuklash faqat `staff` |
| 16 | **Telegram integratsiya** | ✓ Tayyor | Bot token + admin chat ID orqali yangi arizalar real vaqtda adminlarga yetkaziladi; daemon-thread orqali soʻrov bloklanmaydi |

---

## Texnologiyalar

| Kutubxona | Versiya | Maqsad |
|-----------|---------|--------|
| `Django` | `>=5.2, <5.3` | Asosiy freymvork |
| `django-environ` | `>=0.11` | `.env` faylidan muhit oʻzgaruvchilari |
| `django-unfold` | `>=0.40` | Zamonaviy Django admin paneli |
| `django-import-export` | `>=4.0` | Admindan CSV/Excel import-export |
| `django-modeltranslation` | `>=0.19` | Model maydonlarini 3 tilda saqlash |
| `django-ckeditor-5` | `>=0.2.18` | Rich-text muharrir (admin) |
| `django-solo` | `>=2.4` | Yagona qator modellar (SiteConfig) |
| `Pillow` | `>=10.4` | Rasm qayta ishlash |
| `easy-thumbnails` | `>=2.10` | Miniatyuralar yaratish |
| `requests` | `>=2.32` | Telegram API va tashqi soʻrovlar |
| `user-agents` | `>=2.2.0` | Foydalanuvchi agentini tahlil qilish (Analitika) |
| `django-tailwind-cli` | `>=2.20` | Tailwind CSS v4 (Node.js talab qilinmaydi) |
| `whitenoise` | `>=6.7` | Statik fayllarni samarali xizmat qilish |
| `gunicorn` | `>=23.0` | Production WSGI server |
| `tzdata` | — | Windows uchun vaqt zonalari |

**Baza:** SQLite (WAL rejimi — parallel yozuvlarga bardoshli)

---

## Talablar

- **Python 3.13** (yoki 3.11+)
- **Git**
- **Node.js talab qilinmaydi** — Tailwind CSS v4 standalone CLI avtomatik yuklab olinadi

---

## Oʻrnatish

### 1. Repozitoriyani klonlash

```bash
git clone https://github.com/your-org/hopeschool.git
cd hopeschool
```

### 2. Virtual muhit yaratish va aktivlashtirish

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\activate
```

```bash
# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3. Kerakli paketlarni oʻrnatish

```bash
pip install -r requirements.txt
```

### 4. Muhit faylini sozlash

```bash
copy .env.example .env      # Windows
# yoki
cp .env.example .env        # Linux / macOS
```

Keyin `.env` faylini oching va qiymatlarni toʻldiring (quyidagi [jadvalga](#muhit-ozgaruvchilari) qarang).

### 5. Migratsiyalar

```bash
python manage.py migrate
```

### 6. Superuser yaratish

```bash
python manage.py createsuperuser
```

### 7. Tailwind CSS qurilishi

```bash
python manage.py tailwind build
```

> Birinchi ishga tushirishda Tailwind CLI binari avtomatik yuklab olinadi (~5 MB).

### 8. Development serverini ishga tushirish

```bash
python manage.py runserver 127.0.0.1:8001
```

Sayt: [http://127.0.0.1:8001](http://127.0.0.1:8001)
Admin: [http://127.0.0.1:8001/admin/](http://127.0.0.1:8001/admin/)

### 9. Demo maʼlumotlarni yuklash (ixtiyoriy)

```bash
python manage.py seed_demo
```

Bu buyruq kurslar, oʻqituvchilar, yangiliklar, galereya, sertifikatlar va boshqa namunaviy maʼlumotlarni bazaga yuklaydi. Mavjud demo maʼlumotlar avval tozalanadi.

---

## Muhit oʻzgaruvchilari

`.env` faylida quyidagi oʻzgaruvchilar ishlatiladi:

| Oʻzgaruvchi | Majburiy | Standart | Tavsif |
|-------------|----------|----------|--------|
| `DEBUG` | Yoʻq | `True` | Development uchun `True`, production uchun `False` |
| `SECRET_KEY` | **Ha** | — | Django maxfiy kaliti; `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` bilan generatsiya qiling |
| `ALLOWED_HOSTS` | **Ha** | `*` | Vergul bilan ajratilgan domenlar, masalan: `hopeschool.uz,www.hopeschool.uz` |
| `CSRF_TRUSTED_ORIGINS` | Production | — | HTTPS manzillar, masalan: `https://hopeschool.uz` |
| `TELEGRAM_BOT_TOKEN` | Yoʻq | — | Arizalarni yuboruvchi Telegram bot tokeni — toʻldirilmasa bildirishnoma oʻchiriladi |
| `TELEGRAM_ADMIN_CHAT_ID` | Yoʻq | — | Arizalar yuboriladigan chat/guruh ID si (manfiy raqam guruh uchun) |

> **Telegram:** `TELEGRAM_BOT_TOKEN` va `TELEGRAM_ADMIN_CHAT_ID` ikkalasi boʻlishi kerak. Shuningdek, admin panelda **Sayt sozlamalari → "Telegram bildirishnomalari yoniq"** katagini belgilang.

**Namuna `.env`:**

```env
DEBUG=False
SECRET_KEY=your-very-secret-key-here
ALLOWED_HOSTS=hopeschool.uz,www.hopeschool.uz
CSRF_TRUSTED_ORIGINS=https://hopeschool.uz,https://www.hopeschool.uz
TELEGRAM_BOT_TOKEN=1234567890:AAFxxxxxxxxxxxxxx
TELEGRAM_ADMIN_CHAT_ID=-1001234567890
```

---

## Management buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `python manage.py tailwind build` | Tailwind CSS faylini yaratadi (production uchun) |
| `python manage.py tailwind watch` | CSS oʻzgarishlarini kuzatadi (development uchun) |
| `python manage.py tailwind runserver` | `watch` + `runserver` birgalikda ishga tushiradi |
| `python manage.py seed_demo` | Namunaviy maʼlumotlarni bazaga yuklaydi |
| `python manage.py migrate` | Migratsiyalarni qoʻllaydi |
| `python manage.py createsuperuser` | Admin foydalanuvchi yaratadi |
| `python manage.py collectstatic` | Statik fayllarni `staticfiles/` ga yigʻadi (production) |
| `python manage.py makemessages -l ru -l en` | `ru` va `en` uchun `.po` fayllarini yaratadi/yangilaydi |
| `python manage.py compilemessages` | `.po` → `.mo` fayllarini kompilatsiya qiladi (Linux/macOS); Windows da quyidagi eslatmaga qarang |
| `python manage.py prune_visitlogs` | Eski tashrif yozuvlarini oʻchiradi — `--days N` parametri bilan (Analitika; qoʻshilmoqda) |

> **Windows + compilemessages:** GNU `msgfmt` Windows da odatda mavjud emas. Buning oʻrniga `polib` kutubxonasidan foydalaniladi — `.po` fayllarini `.mo` ga aylantirish uchun maxsus skript yoki `polib`-asosidagi yechim ishlatiladi (qarang: `docs/ORNATISH.md`).

---

## Loyiha tuzilishi

```
hopeschool/
├── config/                  # Django konfiguratsiyasi
│   ├── settings.py          #   Asosiy sozlamalar (i18n, DB, Tailwind, Unfold, TELEGRAM)
│   ├── urls.py              #   URL marshrutlar (i18n_patterns + /ariza/ + /i18n/)
│   └── wsgi.py              #   WSGI entry point
│
├── apps/                    # Django ilovalar
│   ├── common/              #   Umumiy abstract modellar, validators, context_processors
│   ├── siteconfig/          #   Sayt sozlamalari (singleton): logo, kontakt, xarita, SEO, analitika
│   ├── pages/               #   Bosh sahifa bloklari: "Biz haqimizda", statistika, "Nega biz"
│   ├── courses/             #   Kurslar va toifalar, kurs detail sahifasi
│   ├── teachers/            #   Oʻqituvchilar profili va detail sahifasi
│   ├── gallery/             #   Galereya albomlari va rasmlari
│   ├── testimonials/        #   Ota-ona fikrlari
│   ├── news/                #   Yangiliklar va eʼlonlar
│   ├── certificates/        #   Sertifikatlar (rasm/PDF/tashqi havola)
│   ├── leads/               #   Ariza formasi, Lead modeli, Telegram signal, sidebar badge
│   └── analytics/           #   VisitLog, middleware, dashboard, prune_visitlogs (qoʻshilmoqda)
│
├── templates/               # Django shablonlar
│   ├── base.html            #   Asosiy shablon (dark mode, toast, modal)
│   └── partials/            #   Header, footer, modal, mobile bar
│
├── static/                  # Statik fayllar (JS, rasm, ikonkalar)
├── assets/                  # Tailwind manba CSS
│   └── css/
│       ├── source.css       #   Tailwind v4 kirish fayli
│       └── tailwind.css     #   Qurilgan CSS chiqish fayli
│
├── locale/                  # .po/.mo tarjima fayllari (ru, en — joriy etilmoqda)
├── media/                   # Yuklangan media fayllar (gitignore)
├── staticfiles/             # collectstatic chiqishi (gitignore)
├── .env.example             # Muhit namuna fayli
├── requirements.txt         # Python bogʻliqliklar
└── manage.py
```

---

## Arizalar va Telegram

> **Holat: tayyor (Phase 3 tugallangan)**

### Ish tartibi

```
Saytdagi ariza formasi  →  POST /ariza/
        │
        ├─ Honeypot tekshiruvi   (bot bo'lsa — 200 OK, lekin saqlanmaydi)
        ├─ IP rate-limit         (1 soatda max 5 ariza — 429 qaytariladi)
        ├─ Forma validatsiyasi   (ismi, +998XXXXXXXXX formati)
        │
        ├─ Lead bazaga saqlanadi
        │       (full_name, phone, course, message, source, status=new)
        │
        └─ post_save signal → transaction.on_commit → daemon thread
                └─ Telegram API: sendMessage (HTML parse_mode)
```

### Admin panel

- **Murojaatlar → Arizalar** — yangi arizalar roʻyxati
- **Sidebar badge** — yangi (holati `new`) arizalar soni dinamik koʻrsatiladi
- Holat ustuni roʻyxatda to'gʻridan-to'gʻri tahririlanadi: `Yangi → Bogʻlanildi → Oʻquvchi boʻldi → Rad etildi`
- `source` maydoni UTM parametr yoki HTTP Referrer dan avtomatik toʻldiriladi

### Telegram bildirishnoma sozlash

1. `.env` da toʻldiring:

   ```env
   TELEGRAM_BOT_TOKEN=1234567890:AAFxxxxxxxxxxxxxx
   TELEGRAM_ADMIN_CHAT_ID=-1001234567890
   ```

2. Admin panelda: **Sayt sozlamalari → Telegram bildirishnomalari yoniq** katagini belgilang.

Agar token yoki chat ID koʻrsatilmagan boʻlsa, bildirishnoma yuborilmaydi — ariza bazaga saqlanadi.

### Spam himoyasi

| Usul | Tavsif |
|------|--------|
| **Honeypot** | Yashirin `website` maydoni — real foydalanuvchilar toʻldirmaydi, botlar toʻldiradi; so jim rad etiladi |
| **IP rate-limit** | Bir IP manzilidan 1 soat ichida 5 tadan ortiq ariza qabul qilinmaydi (Django cache asosida) |
| **Telefon validatsiyasi** | Faqat `+998XXXXXXXXX` formatidagi raqamlar qabul qilinadi |

---

## Tashriflar va Analitika

> **Holat: qoʻshilmoqda (Phase 4)**

`apps/analytics` ilovasi tashrif hisobini middleware darajasida olib boradi — hech qanday JavaScript tracker talab qilinmaydi.

### VisitLog modeli

Har bir saytga kirishda quyidagi maʼlumotlar saqlanadi:

| Maydon | Tavsif |
|--------|--------|
| `ip_address` | Tashrif etuvchining IP manzili (X-Forwarded-For koʻrinadigan) |
| `device_type` | Qurilma turi: desktop / mobile / tablet |
| `browser` | Brauzer nomi (user-agents kutubxonasi orqali) |
| `os` | Operatsion tizim |
| `language` | Soʻralgan til (URL prefiksi asosida: uz/ru/en) |
| `path` | Koʻrilgan sahifa manzili |
| `created_at` | Tashrif vaqti (Asia/Tashkent) |

### Middleware filtrlash

Middleware quyidagi soʻrovlarni **hisobga olmaydi**:

- Botlar va krawlerlar (User-Agent asosida)
- Admin paneli soʻrovlari (`/admin/` prefiksi)
- Statik va media fayllar (`/static/`, `/media/`)

### Admin dashboard

Admin panelda analitika sahifasi quyidagi KPI va grafiklarni koʻrsatadi:

- Jami tashriflar (kunlik/haftalik/oylik)
- Qurilma turi boʻyicha taqsimot (desktop / mobile / tablet)
- Eng koʻp koʻrilgan sahifalar
- Brauzer va OS statistikasi
- Til boʻyicha taqsimot

### `prune_visitlogs` buyruq

Eski VisitLog yozuvlarini oʻchirish uchun management buyruqi:

```bash
# Standart: 90 kundan eski yozuvlarni oʻchiradi
python manage.py prune_visitlogs

# N kun eski yozuvlarni oʻchiradi
python manage.py prune_visitlogs --days 30
```

Ushbu buyruqni crontab yoki systemd timer orqali muntazam ishlatish tavsiya etiladi (masalan, haftada bir marta).

---

## i18n / Tarjima

Sayt **ikki qatlamli** koʻptillilikdan foydalanadi.

### 1. Kontent tarjimasi (django-modeltranslation)

Barcha kontent modellari (kurslar, oʻqituvchilar, yangiliklar va h.k.) uchun har bir matn maydoni uchta versiyada saqlanadi:

```
MODELTRANSLATION_LANGUAGES = ("uz", "ru", "en")
MODELTRANSLATION_DEFAULT_LANGUAGE = "uz"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("uz", "ru", "en")
```

Admin panelda har bir til uchun alohida tab koʻrinadi (`[uz]`, `[ru]`, `[en]`). Biror til uchun maydon boʻsh qolsa, standart — oʻzbekcha — koʻrsatiladi.

URL prefikslari (`i18n_patterns` orqali): `/uz/`, `/ru/`, `/en/`

**Kontent tarjimasi toʻliq ishlaydi** — admindan har til uchun kiritish mumkin.

### 2. Interfeys tarjimasi (gettext / polib)

Admin panel va shablon matnlari `gettext_lazy` bilan belgilangan. Tarjima fayllari quyidagi tuzilmada saqlanadi:

```
locale/
├── ru/
│   └── LC_MESSAGES/
│       ├── django.po    # Ruscha tarjima manba fayli
│       └── django.mo    # Kompilatsiya qilingan fayl
└── en/
    └── LC_MESSAGES/
        ├── django.po
        └── django.mo
```

`.po` fayllari yaratish yoki yangilash:

```bash
python manage.py makemessages -l ru -l en
```

Tarjimalar kiritilgandan soʻng kompilatsiya:

```bash
# Linux / macOS (GNU gettext oʻrnatilgan boʻlsa)
python manage.py compilemessages

# Windows — GNU msgfmt mavjud emas, polib bilan:
python -c "
import polib, pathlib
for po_path in pathlib.Path('locale').rglob('*.po'):
    po = polib.pofile(str(po_path))
    po.save_as_mofile(str(po_path.with_suffix('.mo')))
"
```

> **Windows eslatma:** `compilemessages` buyruqi GNU `msgfmt` dasturini talab qiladi va Windowsda ishlamaydi. `polib` kutubxonasi (`pip install polib`) bu muammoni hal qiladi.

### 3. Til almashtirgich

Saytdagi til almashtirgich Django standart `set_language` koʻrinishiga asoslangan:

```
POST /i18n/set_language/
```

Bu URL `i18n_patterns` dan **tashqarida** joylashgan (`config/urls.py` da `path("i18n/", include("django.conf.urls.i18n"))`) — til almashtirish har qanday sahifadan ishlaydi.

---

## Media xavfsizligi va CKEditor

### Ruxsat etilgan fayl turlari va chegaralar

| Tur | Formatlar | Maks hajm |
|-----|-----------|-----------|
| **Rasm** (modellar) | jpg, jpeg, png, webp, gif | **5 MB** |
| **PDF** (sertifikatlar) | pdf | **10 MB** |
| **CKEditor yuklash** | jpg, jpeg, png, webp, gif | **5 MB** |

Chegaralar `apps/common/validators.py` da `MaxFileSizeValidator` va `FileExtensionValidator` orqali serverda tekshiriladi — faqat client-side emas.

### CKEditor 5

CKEditor 5 quyidagi kontent maydonlarida ishlatiladi:

- Kurs toʻliq tavsifi
- Oʻqituvchi bio
- Yangilik tana qismi
- "Biz haqimizda" matni

**Rasm yuklash huquqi:** Faqat `is_staff=True` boʻlgan foydalanuvchilar CKEditor orqali rasm yuklay oladi (`CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"`).

---

## Deployment

Toʻliq AWS Ubuntu (gunicorn + nginx + systemd) deployment qoʻllanmasi **Phase 7** da qoʻshiladi.

Qisqa eslatma:

```bash
# Production sozlamalari
DEBUG=False
python manage.py collectstatic --noinput
python manage.py migrate

# gunicorn bilan ishga tushirish
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

Qoʻshimcha:
- [`docs/ORNATISH.md`](docs/ORNATISH.md) — batafsil oʻrnatish qoʻllanmasi
- [`docs/ADMIN.md`](docs/ADMIN.md) — kontent boshqaruv qoʻllanmasi
