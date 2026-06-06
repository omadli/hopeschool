# Hope School — Oʻquv Markazi Sayti

> **Bogʻiturkon qishlogʻi (Romitan, Buxoro) uchun zamonaviy ta'lim markazi landing sayti.**
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
9. [Koʻptikillik (i18n)](#koptikillik-i18n)
10. [Deployment](#deployment)

---

## Loyiha haqida

**Hope School** — Buxoro viloyati, Romitan tumani, Bogʻiturkon qishlogʻidagi oʻquv markazi uchun yaratilgan reklama/landing veb-sayt. Sayt potentsial oʻquvchilar va ota-onalarga markaz haqida toʻliq maʼlumot beradi va ariza topshirish imkonini yaratadi.

Asosiy xususiyatlar:

- **Reklama maqsadida** — kurslar, oʻqituvchilar, muvaffaqiyatlar, sertifikatlar va ota-onalar fikrlari orqali markazni taqdim etadi.
- **3 til** — oʻzbek (standart), rus va ingliz tillari qoʻllab-quvvatlanadi; har bir kontent admin paneldan alohida kiritiladi.
- **Toʻliq CMS-boshqaruv** — Django Unfold admin paneli orqali texnik bilimisiz barcha kontent, sozlamalar va arizalar boshqariladi.

---

## Imkoniyatlar

| # | Imkoniyat | Tavsif |
|---|-----------|--------|
| 1 | **Kurslar** | Toifalar bilan kurslar roʻyxati, har bir kurs uchun batafsil sahifa; narx, guruh hajmi, CKEditor tavsif |
| 2 | **Oʻqituvchilar** | Profil sahifasi, tajriba yillari, fanlar, ijtimoiy tarmoq havolalari |
| 3 | **Galereya** | Albomlar tizimi, har bir albomda cheksiz rasm; ALT matn (SEO) |
| 4 | **Yangiliklar va eʼlonlar** | Maqolalar, badge/tag, muqova rasm, chop etish sanasi, SEO meta |
| 5 | **Sertifikatlar** | Oʻquvchi yutuqlari — rasm, PDF yoki tashqi havola bilan |
| 6 | **Ota-ona fikrlari** | Sharh matn, rasm, reyting (1–5), tanlangan belgi |
| 7 | **Statistika bloklari** | Admin paneldan boshqariladigan raqamlar (oʻquvchilar soni, yoʻnalishlar va h.k.) |
| 8 | **"Nega biz" bloklari** | Ikonkali afzallik kartalari, admin orqali tartiblanadi |
| 9 | **Ariza formasi** | Saytdan ariza qabul qilish → bazaga saqlash + Telegram bot bildirishnoma (qoʻshilmoqda) |
| 10 | **Tashrif hisobi** | Xavfsiz tashrif va analitika (keyingi bosqich) |
| 11 | **SEO tayyorligi** | Har bir sahifa uchun meta sarlavha/tavsif, OG rasm; Google, Yandex, Bing webmaster tasdiqlash; GA4, Yandex.Metrica; sitemap |
| 12 | **Xaritadan joylashuv tanlash** | Admin panelda interaktiv Leaflet xarita — belgi bosish yoki manzil qidirish orqali koordinatalar avtomatik toʻladi; Google va Yandex xaritalar shu koordinatalardan quriladi |
| 13 | **Kunduzgi/tungi rejim** | LocalStorage + `prefers-color-scheme` orqali temir-flash yoʻq mavzu almashish |
| 14 | **CKEditor 5 rich-text** | Admin kontent maydonlarida formatlash, rasim yuklash |
| 15 | **Media xavfsizligi** | Rasm: jpg/jpeg/png/webp/gif, maks 5 MB; PDF: 10 MB; CKEditor yuklash faqat `staff` |
| 16 | **Telegram integratsiya** | Bot token + admin chat ID orqali yangi arizalar real vaqtda adminlarga yetkaziladi |

---

## Texnologiyalar

| Kutubxona | Versiya | Maqsad |
|-----------|---------|--------|
| `Django` | `>=5.2, <5.3` | Asosiy freymvork |
| `django-environ` | `>=0.11` | `.env` fayilidan muhit oʻzgaruvchilari |
| `django-unfold` | `>=0.40` | Zamonaviy Django admin paneli |
| `django-import-export` | `>=4.0` | Admindan CSV/Excel import-export |
| `django-modeltranslation` | `>=0.19` | Model maydonlarini 3 tilda saqlash |
| `django-ckeditor-5` | `>=0.2.18` | Rich-text muharrir (admin) |
| `django-solo` | `>=2.4` | Yagona qator modellar (SiteConfig) |
| `Pillow` | `>=10.4` | Rasm qayta ishlash |
| `easy-thumbnails` | `>=2.10` | Miniatyuralar yaratish |
| `requests` | `>=2.32` | Telegram API va tashqi soʻrovlar |
| `user-agents` | `>=2.2.0` | Foydalanuvchi agentini tahlil qilish |
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

Bu buyruq kurslar, oʻqituvchilar, yangiliklar, galereya, sertifikatlar va boshqa namunaviy ma'lumotlarni bazaga yuklaydi. Mavjud demo ma'lumotlar avval tozalanadi.

---

## Muhit oʻzgaruvchilari

`.env` faylida quyidagi oʻzgaruvchilar ishlatiladi:

| Oʻzgaruvchi | Majburiy | Standart | Tavsif |
|-------------|----------|----------|--------|
| `DEBUG` | Yoʻq | `True` | Development uchun `True`, production uchun `False` |
| `SECRET_KEY` | **Ha** | — | Django maxfiy kaliti; `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` bilan generatsiya qiling |
| `ALLOWED_HOSTS` | **Ha** | `*` | Vergul bilan ajratilgan domenlar, masalan: `hopeschool.uz,www.hopeschool.uz` |
| `CSRF_TRUSTED_ORIGINS` | Production | — | HTTPS manzillar, masalan: `https://hopeschool.uz` |
| `TELEGRAM_BOT_TOKEN` | Yoʻq | — | Arizalarni yuboruvchi Telegram bot tokeni ([@BotFather](https://t.me/BotFather) dan olinadi) |
| `TELEGRAM_ADMIN_CHAT_ID` | Yoʻq | — | Arizalar yuboriladigan chat/guruh ID si |

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
| `python manage.py seed_demo` | Namunaviy ma'lumotlarni bazaga yuklaydi |
| `python manage.py migrate` | Migratsiyalarni qoʻllaydi |
| `python manage.py createsuperuser` | Admin foydalanuvchi yaratadi |
| `python manage.py collectstatic` | Statik fayllarni `staticfiles/` ga yigʻadi (production) |
| `python manage.py makemessages -l ru` | `ru` uchun `.po` faylini yaratadi/yangilaydi |
| `python manage.py compilemessages` | `.po` → `.mo` fayllarini kompilatsiya qiladi |

---

## Loyiha tuzilishi

```
hopeschool/
├── config/                  # Django konfiguratsiyasi
│   ├── settings.py          #   Asosiy sozlamalar (i18n, DB, Tailwind, Unfold)
│   ├── urls.py              #   URL marshrutlar (i18n_patterns)
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
│   └── certificates/        #   Sertifikatlar (rasm/PDF/tashqi havola)
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
├── locale/                  # .po/.mo tarjima fayllari (hozircha boʻsh)
├── media/                   # Yuklangan media fayllar (gitignore)
├── staticfiles/             # collectstatic chiqishi (gitignore)
├── .env.example             # Muhit namuna fayli
├── requirements.txt         # Python bogʻliqliklar
└── manage.py
```

---

## Koʻptikillik (i18n)

Sayt **ikki qatlamli** koʻptillilikdan foydalanadi:

### 1. Kontent tarjimasi (django-modeltranslation)

Barcha kontent modellari (kurslar, oʻqituvchilar, yangiliklar va h.k.) uchun har bir matn maydoni uchta versiyada saqlanadi: `uz`, `ru`, `en`. Admin panelda har bir til uchun alohida tab koʻrinadi. URL prefikslari: `/uz/`, `/ru/`, `/en/`.

**Hozirgi holat:** kontent uchun tarjima toʻliq ishlaydi — admindan har til uchun kiritish mumkin.

### 2. Interfeys tarjimasi (gettext)

Admin panel va shablon matinlari `gettext_lazy` bilan belgilangan, lekin `locale/` papkasida `.po`/`.mo` fayllari hali yaratilmagan. Shu sababli `/ru/` va `/en/` prefiksida sahifaga kirilganda interfeys matnlari hozircha **oʻzbekcha** koʻrinadi.

Kelajakda qoʻshish uchun:

```bash
python manage.py makemessages -l ru -l en
# .po fayllarni tarjima qiling
python manage.py compilemessages
```

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

Qoʻshimcha: [`docs/ORNATISH.md`](docs/ORNATISH.md) — batafsil oʻrnatish qoʻllanmasi | [`docs/ADMIN.md`](docs/ADMIN.md) — kontent boshqaruv qoʻllanmasi
