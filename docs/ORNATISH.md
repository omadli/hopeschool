# Oʻrnatish Qoʻllanmasi — Hope School

> Bu qoʻllanma loyihani mahalliy kompyuterda ishga tushirish uchun toʻliq qadamlarni tavsiflab beradi.

---

## Mundarija

1. [Talablar](#talablar)
2. [Repozitoriyani olish](#repozitoriyani-olish)
3. [Virtual muhit](#virtual-muhit)
4. [Paketlarni oʻrnatish](#paketlarni-ornatish)
5. [Muhit faylini sozlash (.env)](#muhit-faylini-sozlash)
6. [Migratsiyalar](#migratsiyalar)
7. [Superuser yaratish](#superuser-yaratish)
8. [Tailwind CSS qurilishi](#tailwind-css-qurilishi)
9. [Development serverini ishga tushirish](#development-serverini-ishga-tushirish)
10. [Demo maʼlumotlar (ixtiyoriy)](#demo-malumotlar)
11. [Muammolarni hal qilish](#muammolarni-hal-qilish)

---

## Talablar

Oʻrnatishdan avval quydagi dasturlar mavjudligini tekshiring:

| Dastur | Versiya | Eslatma |
|--------|---------|---------|
| Python | 3.13 (yoki 3.11+) | `python --version` |
| Git | istalgan | `git --version` |
| pip | 24+ (odatda Python bilan keladi) | `pip --version` |

**Node.js talab qilinmaydi.** Tailwind CSS v4 standalone CLI birinchi ishga tushirishda avtomatik yuklab olinadi.

---

## Repozitoriyani olish

```bash
git clone https://github.com/your-org/hopeschool.git
cd hopeschool
```

---

## Virtual muhit

Virtual muhit yaratish majburiy — bu loyiha paketlarini tizim Pythonidan ajratib turadi.

### Windows (PowerShell)

```powershell
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

Aktivlashtirilganidan keyin terminal satri `(venv)` bilan boshlanishi kerak.

---

## Paketlarni oʻrnatish

```bash
pip install -r requirements.txt
```

Bu buyruq barcha kerakli kutubxonalarni, jumladan Django 5.2, Unfold, modeltranslation, CKEditor 5, Tailwind CLI va gunicorn'ni oʻrnatadi.

---

## Muhit faylini sozlash

`.env.example` faylini `.env` nomi bilan nusxalang:

```powershell
# Windows
copy .env.example .env
```

```bash
# Linux / macOS
cp .env.example .env
```

Keyin `.env` faylini matn muharrirda oching va quyidagi oʻzgaruvchilarni toʻldiring:

```env
# True — dev uchun, False — production uchun
DEBUG=True

# Kuchli tasodifiy kalit (production uchun albatta oʻzgartiring):
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=change-me-to-a-real-secret-key

# Development uchun * qoldirish mumkin
ALLOWED_HOSTS=*

# Production uchun: https://hopeschool.uz
CSRF_TRUSTED_ORIGINS=

# Telegram — ariza yuborish uchun (hozircha ixtiyoriy)
TELEGRAM_BOT_TOKEN=
TELEGRAM_ADMIN_CHAT_ID=
```

### Muhit oʻzgaruvchilari jadvali

| Oʻzgaruvchi | Majburiy | Tavsif |
|-------------|----------|--------|
| `DEBUG` | Yoʻq | `True` — dev, `False` — production |
| `SECRET_KEY` | **Ha** | Django maxfiy kaliti |
| `ALLOWED_HOSTS` | **Ha** | Vergul bilan ajratilgan domenlar |
| `CSRF_TRUSTED_ORIGINS` | Production | HTTPS manzillar |
| `TELEGRAM_BOT_TOKEN` | Yoʻq | Bot tokeni — [@BotFather](https://t.me/BotFather) dan |
| `TELEGRAM_ADMIN_CHAT_ID` | Yoʻq | Arizalar yuboriladigan chat/guruh ID si |

---

## Migratsiyalar

```bash
python manage.py migrate
```

Bu buyruq SQLite bazasini yaratadi (`db.sqlite3`) va barcha jadvallarni tuzadi. Baza WAL rejimida ishlaydi — bu parallel yozuvlarga bardoshliligini oshiradi.

---

## Superuser yaratish

```bash
python manage.py createsuperuser
```

Login, email va parol soʻraladi. Keyin admin panelga kirish uchun shu maʼlumotlardan foydalaning.

---

## Tailwind CSS qurilishi

```bash
python manage.py tailwind build
```

**Birinchi ishga tushirishda** Tailwind CLI binary (~5 MB) avtomatik yuklab olinadi — bu bir marta sodir boʻladi va internet talab qiladi.

### Development rejimida (avtomatik qayta qurilish)

```bash
python manage.py tailwind watch
```

Yoki server va watch'ni birgalikda ishga tushirish:

```bash
python manage.py tailwind runserver
```

---

## Development serverini ishga tushirish

```bash
python manage.py runserver 127.0.0.1:8001
```

> Server **8001**-portda ishga tushadi (8000 boshqa loyiha bilan toʻqnashuv oldini olish uchun).

Brauzerda oching:

| Manzil | Tavsif |
|--------|--------|
| [http://127.0.0.1:8001/](http://127.0.0.1:8001/) | Asosiy sayt (oʻzbekcha) |
| [http://127.0.0.1:8001/ru/](http://127.0.0.1:8001/ru/) | Ruscha versiya |
| [http://127.0.0.1:8001/en/](http://127.0.0.1:8001/en/) | Inglizcha versiya |
| [http://127.0.0.1:8001/admin/](http://127.0.0.1:8001/admin/) | Admin paneli |

---

## Demo Maʼlumotlar

Tez koʻrish uchun namunaviy maʼlumotlarni bazaga yuklash mumkin:

```bash
python manage.py seed_demo
```

Bu buyruq quyidagilarni yaratadi (mavjud demo ma'lumotlar avval oʻchiriladi):

- Sayt sozlamalari (kontaktlar, manzil, Bogʻiturkon koordinatalari)
- 4 ta kurs: Ingliz tili, Matematika, Kimyo, Biologiya
- 4 ta oʻqituvchi profili
- Statistika bloklari (300+ oʻquvchi, 10+ oʻqituvchi va h.k.)
- "Nega biz" afzallik kartalari
- 4 ta ota-ona sharhi
- 3 ta yangilik/eʼlon
- 5 ta sertifikat misoli
- Galereya albomi (gradient namunaviy rasmlar bilan)

> **Diqqat:** `seed_demo` faqat development uchun. Production bazasida ishlatmang.

---

## Muammolarni hal qilish

### `ModuleNotFoundError: No module named 'django'`

Virtual muhit aktivlashtirilmagan. `venv\Scripts\activate` (Windows) yoki `source venv/bin/activate` (Linux) buyruqlarini bajaring.

### Tailwind CLI yuklanmaydi

Internet ulanishi mavjudligini tekshiring. Tailwind CLI bir marta yuklab olinadi va `~/.local/share/tailwind-cli/` (Linux) yoki `%LOCALAPPDATA%\tailwind-cli\` (Windows) papkasida saqlanadi.

### `db.sqlite3` fayli topilmaydi

`python manage.py migrate` buyruqi bajarilmagan. Avval migratsiyalarni ishga tushiring.

### Port 8001 band

```bash
python manage.py runserver 127.0.0.1:8002
```

Boshqa port raqamini belgilang.

### Windows da `'python' is not recognized`

Python PATH ga qoʻshilmagan boʻlishi mumkin. `py` yoki `python3` buyruqlarini sinab koʻring, yoki Python ni qayta oʻrnating va "Add Python to PATH" katagini belgilang.

---

## Keyingi qadam

Oʻrnatish muvaffaqiyatli boʻlgandan soʻng kontent qoʻshishni boshlash uchun [`ADMIN.md`](ADMIN.md) qoʻllanmasini oʻqing.
