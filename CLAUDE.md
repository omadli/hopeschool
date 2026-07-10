# Hope School — loyiha konvensiyalari

## Django template kommentariyalari

**Hech qachon ko'p qatorli `{# … #}` kommentariyadan foydalanmang.**

Django `{# … #}` ni faqat **bitta qatorda** ochilib-yopilganda kommentariya deb
biladi. `{#` bilan `#}` orasida yangi qator (newline) bo'lsa, u kommentariya
sifatida tahlil qilinmaydi — ichidagi matn **render qilingan sahifada ko'rinib
qoladi** (page text sifatida "oqib chiqadi"). Bu bug ilgari ham yuz bergan
(commit `b152226`).

- ✅ Bir qatorli: `{# qisqa izoh, bitta qatorda #}`
- ❌ Ko'p qatorli `{# … #}` — sahifa matni sifatida oqib chiqadi
- Ko'p qatorli izoh kerak bo'lsa `{% comment %} … {% endcomment %}` ishlating
  (masalan `templates/admin/base_site.html` faylining boshidagi bloklar).

## Dev server

Django dev serverni **8000** emas, **8001**-portda ishga tushiring:
`python manage.py runserver 8001`.
