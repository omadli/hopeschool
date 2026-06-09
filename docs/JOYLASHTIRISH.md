# Serverga Joylashtirish (Deploy) — Hope School

> Bu qoʻllanma loyihani Ubuntu serverida (masalan, AWS EC2) ishlab chiqarish
> (production) muhitida ishga tushirishning toʻliq qadamlarini tavsiflaydi:
> **gunicorn + nginx + systemd + Certbot (HTTPS)** + xavfsizlik mustahkamlash va
> **DDoS/rate-limit himoyasi**.

Tayyor konfiguratsiya fayllari `deploy/` papkasida turadi.

---

## Mundarija

1. [Arxitektura](#arxitektura)
2. [Server talablari](#server-talablari)
3. [Foydalanuvchi va kataloglar](#foydalanuvchi-va-kataloglar)
4. [Kodni olish va paketlar](#kodni-olish-va-paketlar)
5. [.env (production)](#env-production)
6. [Baza, statik, tarjima, superuser](#baza-statik-tarjima-superuser)
7. [Xavfsizlik tekshiruvi](#xavfsizlik-tekshiruvi)
8. [gunicorn (systemd)](#gunicorn-systemd)
9. [nginx](#nginx)
10. [HTTPS (Certbot)](#https-certbot)
11. [Geo-IP jadval (systemd timer)](#geo-ip-jadval)
12. [DDoS va rate-limit himoyasi](#ddos-va-rate-limit-himoyasi)
13. [Yangilash (redeploy)](#yangilash-redeploy)
14. [Zaxira nusxa (backup)](#zaxira-nusxa)
15. [Muammolarni hal qilish](#muammolarni-hal-qilish)

---

## Arxitektura

```
Internet ──HTTPS──▶ nginx ──unix socket──▶ gunicorn ──▶ Django (config.wsgi)
                     │                                     │
                     ├─ /static/  → staticfiles/ (nginx)   └─ SQLite (WAL)
                     └─ /media/   → media/      (nginx)
```

- **nginx** — TLS (Certbot), statik/media fayllar, gzip, rate-limit, xavfsizlik headerlari.
- **gunicorn** — Django WSGI ilovasini ishga tushiradi (systemd boshqaradi).
- **whitenoise** faqat *static* fayllarni beradi; *media* (yuklangan rasm/video) ni **nginx** beradi.
- **SQLite (WAL)** — kichik/oʻrta trafik uchun yetarli; Redis talab qilinmaydi.

---

## Server talablari

| Komponent | Versiya / izoh |
|-----------|----------------|
| OS | Ubuntu 22.04 yoki 24.04 LTS |
| Python | 3.11+ (`python3 --version`) |
| nginx | `sudo apt install nginx` |
| Certbot | `sudo apt install certbot python3-certbot-nginx` |
| fail2ban | `sudo apt install fail2ban` (IP bloklash) |
| Domen | `hopeschool.uz` A-yozuvi server IP ga yoʻnaltirilgan |

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx fail2ban git
```

---

## Foydalanuvchi va kataloglar

Ilova uchun alohida (login qila olmaydigan) tizim foydalanuvchisi yaratamiz:

```bash
sudo adduser --system --group --home /home/hopeschool hopeschool
sudo mkdir -p /home/hopeschool/app
sudo chown hopeschool:www-data /home/hopeschool/app
```

> `deploy/` ichidagi fayllar `/home/hopeschool/app` yoʻlini va `hopeschool`
> foydalanuvchisini nazarda tutadi. Boshqa yoʻl tanlasangiz, fayllardagi
> yoʻllarni mos ravishda oʻzgartiring.

---

## Kodni olish va paketlar

```bash
sudo -u hopeschool -H bash
cd /home/hopeschool/app
git clone https://github.com/your-org/hopeschool.git .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## .env (production)

```bash
cp .env.example .env
nano .env
```

Production uchun **majburiy** qiymatlar:

```env
DEBUG=False

# Kuchli kalit yarating:
#   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=<yangi-kuchli-kalit>

# Aniq domenlar — '*' EMAS
ALLOWED_HOSTS=hopeschool.uz,www.hopeschool.uz
CSRF_TRUSTED_ORIGINS=https://hopeschool.uz,https://www.hopeschool.uz

TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_ADMIN_CHAT_ID=<chat-id>
```

> **Diqqat:** `DEBUG=False` boʻlganda `settings.py` xavfsizlik bloki yoqiladi.
> Agar `SECRET_KEY` hali ham dev qiymati boʻlsa yoki `ALLOWED_HOSTS=*` boʻlsa,
> Django **ishga tushishdan bosh tortadi** (xato bilan) — bu ataylab shunday,
> xavfli sozlama bilan deploy boʻlib qolmaslik uchun.

> **HSTS haqida:** birinchi HTTPS deployda `.env` ga `SECURE_HSTS_SECONDS=3600`
> qoʻying. TLS barqaror ishlayotganiga ishonch hosil qilgach, qiymatni
> `31536000` (1 yil) ga koʻtaring. HSTS brauzerda keshlanadi — uni orqaga
> qaytarish qiyin.

---

## Baza, statik, tarjima, superuser

```bash
# venv aktiv, /home/hopeschool/app da
python manage.py migrate
python manage.py createcachetable          # rate-limit uchun umumiy cache jadvali
python manage.py collectstatic --noinput   # → staticfiles/
python manage.py tailwind build            # → assets/css/tailwind.css
python manage.py createsuperuser

# i18n (.mo) — bu serverda gettext oʻrnatilgan boʻlsa:
python manage.py compilemessages
# gettext yoʻq boʻlsa (polib bilan):
python -c "import polib, pathlib; [polib.pofile(str(p)).save_as_mofile(str(p.with_suffix('.mo'))) for p in pathlib.Path('locale').rglob('*.po')]"
```

Kataloglarga yozish huquqini taʼminlang:

```bash
exit   # hopeschool sessiyasidan chiqing (agar sudo -u bilan kirgan boʻlsangiz)
sudo chown -R hopeschool:www-data /home/hopeschool/app
sudo chmod -R g+rwX /home/hopeschool/app/media
```

---

## Xavfsizlik tekshiruvi

Django joylashtirishdan oldin sozlamalarni tekshiradi:

```bash
DEBUG=False SECRET_KEY=$(grep SECRET_KEY .env | cut -d= -f2) \
ALLOWED_HOSTS=hopeschool.uz python manage.py check --deploy
```

Natija **"System check identified no issues"** boʻlishi kerak. Loyiha bu
tekshiruvni avtomatlashtirilgan testda ham ushlab turadi
(`apps/common/test_deploy.py`).

---

## gunicorn (systemd)

```bash
sudo cp /home/hopeschool/app/deploy/gunicorn.service /etc/systemd/system/gunicorn.service
# Unit sintaksisini tekshiring:
systemd-analyze verify /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
sudo systemctl status gunicorn          # active (running) boʻlishi kerak
journalctl -u gunicorn -f               # loglar
```

gunicorn unix-socketni `/run/hopeschool/gunicorn.sock` da yaratadi
(`deploy/gunicorn.conf.py`). Worker sonini `.env` da `GUNICORN_WORKERS` bilan
sozlash mumkin (SQLite uchun 2–3 yetarli).

---

## nginx

```bash
# Rate-limit zonalari (http kontekstida — conf.d ga):
sudo cp /home/hopeschool/app/deploy/nginx-ratelimit.conf /etc/nginx/conf.d/hopeschool-ratelimit.conf
# Sayt konfiguratsiyasi:
sudo cp /home/hopeschool/app/deploy/nginx.conf /etc/nginx/sites-available/hopeschool
sudo ln -s /etc/nginx/sites-available/hopeschool /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

---

## HTTPS (Certbot)

```bash
sudo certbot --nginx -d hopeschool.uz -d www.hopeschool.uz
```

Certbot `nginx.conf` ni avtomatik tahrirlaydi: 443-portli TLS bloki va
HTTP→HTTPS yoʻnaltirishni qoʻshadi. Sertifikat avtomatik yangilanadi
(`systemctl status certbot.timer`).

HTTPS ishlagach, kerak boʻlsa `nginx.conf` dagi **CSP** (Content-Security-Policy)
blokini izohdan chiqaring va brauzer konsolida har bir sahifani tekshiring
(barcha tashqi resurslar — shriftlar, xaritalar, video — ishlashini).

---

## Geo-IP jadval

Dashboarddagi "Davlatlar boʻyicha tashriflar" paneli `resolve_geoip` buyruq
ishlamaguncha boʻsh boʻladi. Uni 30 daqiqada bir avtomatik ishlatamiz:

```bash
sudo cp /home/hopeschool/app/deploy/resolve-geoip.service /etc/systemd/system/
sudo cp /home/hopeschool/app/deploy/resolve-geoip.timer   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now resolve-geoip.timer
sudo systemctl list-timers resolve-geoip.timer
```

---

## DDoS va rate-limit himoyasi

Himoya **uch qatlamda** qurilgan:

### 1-qatlam — Ilova darajasi (allaqachon yoqilgan)
- **Honeypot** maydoni — botlar ariza formasini toʻldirsa, jimgina rad etiladi.
- **IP rate-limit** — bitta IP dan soatiga 5 tadan ortiq ariza qabul qilinmaydi
  (`apps/leads/views.py`). Hisoblagich **umumiy cache** (DatabaseCache) da
  saqlanadi, shuning uchun barcha gunicorn worker'lar boʻylab toʻgʻri ishlaydi.

### 2-qatlam — nginx (chekka/edge)
`deploy/nginx-ratelimit.conf` quyidagi cheklovlarni qoʻyadi (limit oshsa **429**):

| Zona | Cheklov | Qayerda |
|------|---------|---------|
| `hs_general` | 20 soʻrov/sek (burst 40) | barcha sahifalar |
| `hs_form` | 10 soʻrov/daq (burst 5) | `POST /ariza/` |
| `hs_login` | 20 soʻrov/daq (burst 10) | `/admin/login/` |
| `hs_conn` | 20 parallel ulanish/IP | barchasi (slow-loris) |

### 3-qatlam — fail2ban (firewall darajasida IP bloklash)
nginx loglarini kuzatib, cheklovni qayta-qayta buzgan IP larni **iptables**
darajasida bloklaydi — keyingi trafik nginx gacha ham yetib bormaydi.

```bash
sudo cp /home/hopeschool/app/deploy/fail2ban/filter.d/hopeschool-nginx-429.conf /etc/fail2ban/filter.d/
sudo cp /home/hopeschool/app/deploy/fail2ban/jail.d/hopeschool.conf /etc/fail2ban/jail.d/
# O'z IP manzilingizni jail.d/hopeschool.conf ichidagi `ignoreip` ga qo'shing!
# Filtr regex'ini haqiqiy logga moslab tekshiring (0 ta match boʻlsa, format farq qiladi):
sudo fail2ban-regex /var/log/nginx/access.log /etc/fail2ban/filter.d/hopeschool-nginx-429.conf
sudo systemctl enable --now fail2ban
sudo fail2ban-client status                      # jail roʻyxati
sudo fail2ban-client status hopeschool-nginx-429 # bloklangan IP lar
sudo fail2ban-client set <jail> unbanip 1.2.3.4  # qoʻlda blokdan chiqarish
```

### Hajmli (volumetric) DDoS haqida muhim eslatma
Yuqoridagi himoyalar **ilova darajasidagi** suiisteʼmol (spam, brute-force,
sekin floodlar) ga qarshi samarali. Ammo **katta hajmli L3/L4 DDoS** (kanalni
toʻldiradigan) ni bitta server yoki nginx **toʻxtata olmaydi** — buning uchun
saytni quyidagilar orqasiga qoʻyish kerak:

- **Cloudflare** (bepul reja ham DDoS himoyasi + WAF beradi) — eng oson yechim,
- yoki **AWS Shield / CloudFront / WAF** (AWS da hosting boʻlsa),
- yoki provayder/CDN darajasidagi himoya.

> Tavsiya: domenni **Cloudflare** orqali ulang (proxy yoqilgan) — bu volumetric
> DDoS, bot himoyasi va keshlashni bir vaqtda beradi.

> **Cloudflare ishlatsangiz:** endi nginx oldida yana bitta proksi turadi, shuning
> uchun `.env` ga `TRUSTED_PROXY_COUNT=2` qoʻshing. Bu ariza rate-limiti
> `X-Forwarded-For` dan **haqiqiy** mijoz IP sini toʻgʻri olishini taʼminlaydi
> (aks holda barcha tashriflar Cloudflare IP si sifatida koʻrinib, rate-limit
> notoʻgʻri ishlaydi). Standart qiymat `1` (faqat nginx).

---

## Yangilash (redeploy)

```bash
sudo -u hopeschool -H bash
cd /home/hopeschool/app && source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py tailwind build
python manage.py compilemessages   # yoki polib skripti
exit
sudo systemctl restart gunicorn
```

---

## Zaxira nusxa

SQLite bazasi va yuklangan media — eng muhim maʼlumotlar:

```bash
# Baza (WAL rejimida xavfsiz nusxa olish uchun .backup ishlating):
sqlite3 /home/hopeschool/app/db.sqlite3 ".backup '/home/hopeschool/backups/db-$(date +%F).sqlite3'"
# Media fayllar:
tar czf /home/hopeschool/backups/media-$(date +%F).tar.gz -C /home/hopeschool/app media
```

> Bu buyruqlarni `cron` yoki systemd timer orqali kunlik avtomatlashtiring, va
> nusxalarni boshqa joyga (S3 va h.k.) koʻchiring.

---

## Muammolarni hal qilish

### 502 Bad Gateway
gunicorn ishlamayapti yoki socketga ruxsat yoʻq.
```bash
sudo systemctl status gunicorn
journalctl -u gunicorn -n 50
ls -l /run/hopeschool/gunicorn.sock     # www-data oʻqiy olishi kerak
```

### Statik fayllar (CSS) yuklanmayapti
`collectstatic` bajarilmagan yoki nginx `alias` yoʻli notoʻgʻri.
```bash
python manage.py collectstatic --noinput
ls /home/hopeschool/app/staticfiles/css/tailwind.css
```

### Yuklangan rasm/video koʻrinmayapti (404)
nginx `/media/` `alias` yoʻlini va kataloq ruxsatlarini tekshiring.

### `DisallowedHost` xatosi
`.env` dagi `ALLOWED_HOSTS` ga domeningiz kiritilmagan.

### Ariza yuborilganda 429
Rate-limit ishlayapti — bu normal. Test uchun cache jadvalini tozalang:
`python manage.py shell -c "from django.core.cache import cache; cache.clear()"`

### `manage.py check --deploy` xato beryapti
Xato matnini oʻqing — odatda `SECRET_KEY` zaif yoki `ALLOWED_HOSTS=*`.

---

## Bogʻliq qoʻllanmalar

- [`ORNATISH.md`](ORNATISH.md) — mahalliy (dev) oʻrnatish
- [`ADMIN.md`](ADMIN.md) — admin panelda kontent boshqaruvi
