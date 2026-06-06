# Admin Paneli — Kontent Boshqaruv Qoʻllanmasi

> Bu qoʻllanma Hope School admin paneli orqali sayt kontentini boshqarishni tavsiflab beradi.
> Texnik bilim talab qilinmaydi — barcha amallar forma orqali bajariladi.

**Admin paneli manzili:** `http://saytmanzili/admin/`

---

## Mundarija

1. [Admin paneliga kirish](#admin-paneliga-kirish)
2. [Umumiy tamoyillar](#umumiy-tamoyillar)
3. [Sayt sozlamalari](#sayt-sozlamalari)
4. [Bosh sahifa bloklari](#bosh-sahifa-bloklari)
5. [Kurslar](#kurslar)
6. [Oʻqituvchilar](#oʻqituvchilar)
7. [Yangiliklar va eʼlonlar](#yangiliklar-va-eʼlonlar)
8. [Galereya](#galereya)
9. [Sertifikatlar](#sertifikatlar)
10. [Ota-ona fikrlari](#ota-ona-fikrlari)
11. [Arizalar](#arizalar)
12. [Uch til bilan ishlash](#uch-til-bilan-ishlash)
13. [CKEditor — boy matn muharriri](#ckeditor--boy-matn-muharriri)
14. [Tartiblashtirish va yashirish](#tartiblashtirish-va-yashirish)

---

## Admin paneliga kirish

1. Brauzerda `http://127.0.0.1:8001/admin/` manzilini oching
2. Login va parolni kiriting (oʻrnatish vaqtida `createsuperuser` bilan yaratilgan)
3. Chap tomonli menyu orqali boʻlimlarga oʻting

Yuqori oʻng burchakdagi **"Saytni koʻrish"** tugmasi asosiy saytga oʻtishga imkon beradi.

---

## Umumiy tamoyillar

### Saqlash tugmalari

Har bir forma pastki qismida uchta tugma bor:

| Tugma | Tavsif |
|-------|--------|
| **Saqlash va davom etish** | Saqlaydi, shu sahifada qoladi |
| **Saqlash va yangi qoʻshish** | Saqlaydi, boʻsh forma ochadi |
| **Saqlash** | Saqlaydi va roʻyxatga qaytadi |

### Tarix (History)

Har bir obʼekt sahifasida **"Tarix"** tugmasi bor — kimdir oʻzgartirgan barcha amallarni koʻrish mumkin.

### "Saytda koʻrsatilsin" maydoni

Koʻp modellar "**Saytda koʻrsatilsin**" katagiga ega. Belgini olib tashlash uchun mazmunan saytdan yashiriladi, lekin bazadan oʻchirilmaydi.

### Tartib raqami

"**Tartib raqami**" maydoni kichikroq son = yuqoroqda koʻrinadi. Masalan, 0 → birinchi, 10 → oxirgi.

---

## Sayt sozlamalari

**Admin menyusi → Sozlamalar → Sayt sozlamalari**

Bu yagona forma — barcha global sayt maʼlumotlari shu yerda saqlanadi.

### Brending

| Maydon | Tavsif |
|--------|--------|
| **Sayt nomi** | Sarlavhada va admin panelda koʻrinadigan nom |
| **Shior** | Qisqa tavsif (header yoki hero da ishlatilishi mumkin) |
| **Logo** | Sayt logotipi — JPG/PNG/WebP/GIF, maks 5 MB |
| **Favicon** | Brauzer yorliqcha ikonkasi |
| **Domen** | `hopeschool.uz` (protokolsiz) — sitemap va canonical uchun |

### Kontaktlar

| Maydon | Tavsif |
|--------|--------|
| **Asosiy telefon** | +998 XX XXX XX XX formatida |
| **Qoʻshimcha telefon** | Ikkinchi raqam (ixtiyoriy) |
| **Email** | Bogʻlanish email manzili |
| **Manzil** | Toʻliq pochta manzili |
| **Ish vaqti** | Masalan: Dush–Shan, 09:00–18:00 |

### Joylashuv — Xaritadan tanlash

Bu boʻlimda interaktiv **Leaflet xarita** (OpenStreetMap asosida) koʻrinadi. API kalit talab qilinmaydi.

**Joylashuvni belgilash usullari:**

1. **Qidiruv orqali:** "Manzilni qidiring" maydoniga qishloq/shahar nomini kiriting → "Qidirish" tugmasini bosing → natijalar koʻrsatiladi
2. **Xaritani bosish orqali:** Xarita ustiga bosing — belgi (pin) shu joyga qoʻyiladi
3. **Belgini sudrab:** Belgini xaritada istalgan joyga suring

Joylashuv tanlanganida **Kenglik (lat)** va **Uzunlik (lng)** maydonlari avtomatik toʻladi. Bu koordinatalardan Google Xarita va Yandex Xarita havolalari avtomatik quriladi.

> **Eslatma:** "Xarita — qoʻlda override" boʻlimi odatda boʻsh qoldiriladi — faqat maxsus embed kodi kerak boʻlsa toʻldiring.

### Ijtimoiy tarmoqlar

Instagram, Telegram kanal, Telegram guruh, YouTube, Facebook va TikTok havolalarini kiriting. Boʻsh qoldirilgan tarmoqlar saytda koʻrsatilmaydi.

### SEO sozlamalari

| Maydon | Tavsif |
|--------|--------|
| **SEO sarlavha** | Brauzer yorliqcha va qidiruv natijalarida koʻrinadigan nom (maks 60 belgi tavsiya etiladi) |
| **SEO tavsif** | Qidiruv natijalarida tavsif (maks 160 belgi tavsiya etiladi) |
| **OG rasm** | Ijtimoiy tarmoqlarda ulashilganda koʻrinadigan rasm (1200×630 px tavsiya etiladi) |
| **Google verification** | Google Search Console dan olingan `content` qiymati |
| **Yandex verification** | Yandex Webmaster dan olingan tasdiqlash kodi |
| **Bing verification** | Bing Webmaster dan olingan tasdiqlash kodi |

### Analitika ID lari

| Maydon | Format | Tavsif |
|--------|--------|--------|
| **Google Analytics 4 ID** | `G-XXXXXXXXXX` | GA4 oʻlchov identifikatori |
| **Yandex Metrica ID** | Raqam | Yandex Metrica schetchik raqami |

### Telegram bildirishnomalari

"**Telegram bildirishnomalari yoniq**" katagini belgilash yoki olib tashlash orqali arizalarning Telegram ga yuborilishini boshqarish mumkin (TELEGRAM_BOT_TOKEN va TELEGRAM_ADMIN_CHAT_ID `.env` da toʻldirilgan boʻlishi kerak).

---

## Bosh sahifa bloklari

### Biz haqimizda boʻlimi

**Admin menyusi → Bosh sahifa bloklari → Biz haqimizda**

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Asosiy sarlavha (masalan: "Bilim — ishonch — kelajak") |
| **Kichik sarlavha** | Yuqori qism belgisi (masalan: "Biz haqimizda") |
| **Matn** | CKEditor bilan boy matn, formatlashtirish imkoni bor |
| **Rasm** | Tasvir rasmi |

Faqat birinchi faol yozuv saytda koʻrsatiladi.

---

### Statistika raqamlari

**Admin menyusi → Bosh sahifa bloklari → Statistika**

Bosh sahifada animatsiyali hisoblagich raqamlari:

| Maydon | Tavsif |
|--------|--------|
| **Raqam** | Butun son (masalan: 300) |
| **Belgi** | Qoʻshimcha belgi — `+`, `%`, `k` va h.k. |
| **Izoh** | Raqam tagidagi matn (masalan: "Oʻquvchilar") |
| **Qizil rang bilan** | Belgilansa, urgʻu rangida koʻrsatiladi |
| **Tartib raqami** | Koʻrinish tartibi |

---

### "Nega biz" kartalari

**Admin menyusi → Bosh sahifa bloklari → Nega biz**

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Karta sarlavhasi |
| **Tavsif** | Qisqa izoh |
| **Ikonka** | Ikonka kodi — mavjud variantlardan tanlang |
| **Qizil ikonka** | Belgisiz — standart, belgilansa — urgʻu rangi |

---

## Kurslar

**Admin menyusi → Sayt mazmuni → Kurslar**

### Kurs turkumlarini boshqarish

Kurslardan oldin turkumlarni (toifalarni) yarating:

**Kurs turkumlari → Qoʻshish**

| Maydon | Tavsif |
|--------|--------|
| **Nomi** | Turkum nomi (masalan: "Til", "Aniq fan") |
| **Slug** | URL uchun nom — avtomatik toʻldiriladi |

### Yangi kurs qoʻshish

**Kurslar → Qoʻshish**

| Maydon | Tavsif |
|--------|--------|
| **Nomi** | Kurs nomi |
| **Slug** | URL manzil (avtomatik yoki qoʻlda) |
| **Turkum** | Yuqorida yaratilgan toifadan tanlang |
| **Qisqa tavsif** | Kurslar roʻyxatida koʻrinadigan qisqa matn (maks 255 belgi) |
| **Toʻliq tavsif** | CKEditor bilan boy matn — kurs detail sahifasida |
| **Davomiyligi** | Erkin matn (masalan: "6 oy", "Doimiy qabul") |
| **Guruh hajmi** | Masalan: "15 kishi", "6–10" |
| **Narx** | Raqam (ixtiyoriy) |
| **Narx izohi** | Masalan: "soʻm/oy" |
| **Narx koʻrsatilsin** | Belgilanmasa narx saytda yashirinadi |
| **Ikonka** | Vizual belgi kodi |
| **Rasm** | Kurs rasmi — JPG/PNG/WebP, maks 5 MB |
| **Top kurs** | Belgilansa, kursda maxsus urgʻu koʻrsatiladi |
| **SEO sarlavha** | Ushbu kurs sahifasi uchun maxsus sarlavha (boʻsh qolsa umumiy ishlatiladi) |
| **SEO tavsif** | Ushbu kurs uchun meta tavsif |

**Til tablari (uz / ru / en):** Har bir matn maydon uchta versiyada kiritiladi (qarang: [Uch til bilan ishlash](#uch-til-bilan-ishlash)).

---

## Oʻqituvchilar

**Admin menyusi → Sayt mazmuni → Oʻqituvchilar**

| Maydon | Tavsif |
|--------|--------|
| **F.I.Sh.** | Toʻliq ismi |
| **Slug** | URL uchun (avtomatik) |
| **Rasm** | Oʻqituvchi surati — JPG/PNG/WebP, maks 5 MB |
| **Lavozim / yoʻnalish** | Qisqa tavsif (masalan: "Ingliz tili · C1 daraja") |
| **Bio / tavsif** | CKEditor bilan toʻliq biografiya |
| **Fanlar** | Oʻqitiladigan fanlar roʻyxati |
| **Tajriba (yil)** | Ish tajribasi yillarda |
| **Instagram** | Instagram profil havolasi |
| **Telegram** | Shaxsiy Telegram havolasi |
| **YouTube** | YouTube kanal havolasi |
| **SEO sarlavha / tavsif** | Profil sahifasi uchun meta maʼlumotlar |

---

## Yangiliklar va Eʼlonlar

**Admin menyusi → Sayt mazmuni → Yangiliklar**

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Yangilik/eʼlon sarlavhasi |
| **Slug** | URL (avtomatik) |
| **Qisqa matn** | Roʻyxatda koʻrinadigan annotatsiya (maks 300 belgi) |
| **Toʻliq matn** | CKEditor bilan boy mazmun — maqola tana qismi |
| **Muqova rasmi** | Asosiy rasm — JPG/PNG/WebP, maks 5 MB |
| **Belgi (tag)** | Qisqa yorliq (masalan: "Eʼlon", "Yangilik", "Aksiya", "Tadbir") |
| **Qizil belgi** | Belgilansa, tag urgʻu rangida koʻrsatiladi |
| **Chop etilgan sana** | Avtomatik toʻldiriladi, qoʻlda oʻzgartirish mumkin |
| **Chop etilgan** | Belgisi olib tashlansa, maqola saytda koʻrinmaydi |
| **Tanlangan** | Belgilansa, sahifada alohida koʻrsatilishi mumkin |

---

## Galereya

**Admin menyusi → Sayt mazmuni → Galereya**

Galereya ikki qatlamdan iborat: **Albom** → **Rasmlar**.

### Albom yaratish

**Galereya albomlari → Qoʻshish**

| Maydon | Tavsif |
|--------|--------|
| **Albom nomi** | Masalan: "Oʻquv jarayoni", "Tadbir — 2025" |
| **Slug** | URL (avtomatik) |
| **Tavsif** | Qisqa izoh |
| **Muqova rasmi** | Albomni ifodalovchi rasm |

### Albomga rasm qoʻshish

Albomni ochib **"Rasmlar"** boʻlimida rasmlarni qoʻshing:

| Maydon | Tavsif |
|--------|--------|
| **Rasm** | JPG/PNG/WebP/GIF, maks 5 MB |
| **Izoh** | Rasm tagida koʻrinadigan matn |
| **ALT matn (SEO)** | Qidiruv tizimi va maxsus imkoniyatlar uchun tavsif |
| **Tartib raqami** | Koʻrsatish tartibi |

---

## Sertifikatlar

**Admin menyusi → Sayt mazmuni → Sertifikatlar**

Oʻquvchilar muvaffaqiyatlari va sertifikatlarini namoyish etish uchun.

| Maydon | Tavsif |
|--------|--------|
| **Sarlavha** | Sertifikat nomi (masalan: "Aziza R. — IELTS Band 7.0") |
| **Oʻquvchi ismi** | Sertifikat egasining ismi |
| **Izoh** | Qisqa tavsif (masalan: "IELTS Band 7.0", "Kimyo olimpiadasi gʻolibi") |
| **Belgi** | Qisqa yorliq (masalan: "IELTS", "SAT", "Gʻolib") |
| **Qizil belgi** | Belgilansa, urgʻu rangida koʻrsatiladi |
| **Rasm** | Sertifikat tasvirining surati |
| **PDF fayl** | Sertifikat PDF nusxasi (maks 10 MB) |
| **Tashqi havola** | Masalan: Telegram kanal havolasi |

> **Diqqat:** Rasm, PDF yoki tashqi havoladan kamida bittasi kiritilishi **majburiy**.

---

## Ota-ona Fikrlari

**Admin menyusi → Sayt mazmuni → Fikrlar**

| Maydon | Tavsif |
|--------|--------|
| **Muallif** | Ismi (masalan: "Dildora opa") |
| **Roli** | Masalan: "Ona", "Ota · 8-sinf oʻquvchisining otasi" |
| **Fikr matni** | Asosiy sharh matni |
| **Rasm** | Muallif surati (ixtiyoriy) |
| **Baho (1–5)** | Reyting yulduzchalari |
| **Tanlangan** | Belgilansa, alohida ajratib koʻrsatilishi mumkin |

---

## Arizalar

**Ariza formasi va Telegram integratsiya qoʻshilmoqda (Phase 3).**

Saytning bosh sahifasida ariza topshirish formasi mavjud. Ariza yuborilganda:

1. **Bazaga saqlanadi** — admin paneldagi "Arizalar" boʻlimida koʻrish mumkin
2. **Telegram ga yuboriladi** — `.env` da `TELEGRAM_BOT_TOKEN` va `TELEGRAM_ADMIN_CHAT_ID` toʻldirilgan boʻlsa

Telegram bildirishnomalarini yoqish/oʻchirish: **Sayt sozlamalari → Telegram → "Telegram bildirishnomalari yoniq"** katagini boshlash.

---

## Uch Til bilan Ishlash

Sayt uch tilda ishlaydi: **oʻzbek (uz)**, **rus (ru)** va **ingliz (en)**.

### Kontent maydonlari

Matn kiritish maydonlari admin formada uch guruhga ajratilgan:

```
[ uz tab ]  [ ru tab ]  [ en tab ]
```

Har bir tabda oʻsha til uchun matn kiritiladi. Masalan, kurs nomini uch tilda kiritish:

- **uz tab:** "Ingliz tili"
- **ru tab:** "Английский язык"
- **en tab:** "English Language"

Agar biror til uchun maydon boʻsh qolsa, standart til (oʻzbekcha) matn koʻrsatiladi.

### URL prefikslari

| URL | Til |
|-----|-----|
| `/uz/` | Oʻzbekcha |
| `/ru/` | Ruscha |
| `/en/` | Inglizcha |

### Interfeys tarjimasi haqida eslatma

Hozirgi bosqichda admin interfeysi va sahifa matinlari oʻzbekcha. `/ru/` yoki `/en/` prefiksida saytga kirilsa, **kontent** oʻsha tilda koʻrsatiladi (admindan kiritilgan), lekin navigatsiya tugmalari va interfeys elementlari hali oʻzbekcha — chunki `.po` tarjima fayllari hali yaratilmagan.

---

## CKEditor — Boy Matn Muharriri

CKEditor 5 quyidagi kontentlar uchun ishlatiladi:
- Kurs toʻliq tavsifi
- Oʻqituvchi bio
- Yangilik tana qismi
- "Biz haqimizda" matni

### Imkoniyatlar

| Funksiya | Tavsif |
|----------|--------|
| **Sarlavhalar** | H1, H2, H3 darajali sarlavhalar |
| **Qalin / kursiv / tagiga chizilgan** | Urgʻu berish |
| **Havola** | Tashqi va ichki havolalar |
| **Roʻyxat** | Nuqtali va raqamli roʻyxatlar |
| **Iqtibos** | Block quote |
| **Rasm yuklash** | Bevosita muharrirga rasm yuklash |
| **Bekor qilish / qaytarish** | Ctrl+Z / Ctrl+Y |

### Rasm yuklash chegaralari (CKEditor orqali)

- Faqat `staff` (xodim) maqomidagi foydalanuvchilar rasm yuklay oladi
- Ruxsat etilgan formatlar: **JPG, JPEG, PNG, WebP, GIF**
- Maksimal hajm: **5 MB**

---

## Tartiblashtirish va Yashirish

### Tartib raqami

Har bir kontent modelida "**Tartib raqami**" maydoni bor:

- **0** — eng yuqorida koʻrsatiladi
- **10, 20, 30...** — pastroqda koʻrsatiladi
- Bir xil raqam boʻlsa, yaratilgan vaqtga koʻra tartiblanadi

Masalan, kurslarni tartiblashtirish uchun "Ingliz tili"ga `0`, "Matematika"ga `1`, "Kimyo"ga `2` kiriting.

### Yashirish (oʻchirmasdan)

"**Saytda koʻrsatilsin**" belgisini olib tashlang — element bazadan oʻchirilmaydi, faqat saytda koʻrinmaydi. Keyinchalik qayta yoqish mumkin.

### Roʻyxatda tezkor amallar

Admin roʻyxat sahifasida elementni tanlagan holda:
- **Yashirish** — tanlangan elementlarni bir anda yashirish
- **Koʻrsatish** — tanlangan elementlarni bir anda yoqish
- **Oʻchirish** — doimiy oʻchirish (ehtiyot boʻling!)

---

## Tez-tez beriladigan savollar

**Kontent oʻzgarishlar saytda darhol koʻrinmaydimi?**
Ha, saqlashdan soʻng darhol yangilanadi. Kesh muammosi boʻlsa brauzerda Ctrl+F5 bosing.

**Logoni qanday almashtiriladi?**
Sayt sozlamalari → Brending → Logo → fayl yuklang → Saqlang.

**Yangi foydalanuvchi (admin) qanday yaratiladi?**
Admin paneli → Sozlamalar → Foydalanuvchilar → Qoʻshish. "Xodim maqomi" va "Superuser maqomi" kataglarini belgilang.

**Kontent oʻchib ketgan, qaytarish mumkinmi?**
Har bir elementning "Tarix" sahifasida oldingi versiyalarni koʻrish mumkin, lekin avtomatik tiklash funksiyasi hozircha yoʻq. Muhim oʻzgarishlardan oldin bazani zahiralang.
