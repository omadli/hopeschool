"""Hope School — REAL content seed.

All data below is sourced from the school's own public Telegram channel
(@Hope_school_channel, formerly @Hope_academy7) and group (@hope_school_group):
real teachers, real courses/prices/schedules, real student results (name +
level + score, each linking to the original channel post for proof) and real
classroom photos. No fabricated names, testimonials, or statistics.

Re-running clears the demo content tables (NOT leads) and recreates them.
"""
from datetime import datetime
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone, translation

from apps.certificates.models import Certificate
from apps.courses.models import Course, CourseCategory
from apps.gallery.models import GalleryAlbum, GalleryImage, GalleryVideo
from apps.news.models import NewsPost
from apps.pages.models import AboutSection, SiteCopy, StatItem, WhyUsItem
from apps.siteconfig.models import SiteConfig, SocialLink
from apps.teachers.models import Teacher
from apps.testimonials.models import Testimonial

# apps/common/seed_assets/  (committed real photos downloaded from the channel)
ASSETS = Path(__file__).resolve().parents[2] / "seed_assets"
CHANNEL = "https://t.me/Hope_school_channel"


def load_img(relpath):
    """Read a committed seed image into a ContentFile for an ImageField."""
    p = ASSETS / relpath
    return p.name, ContentFile(p.read_bytes())


class Command(BaseCommand):
    help = "Hope School saytini kanal/guruhdan olingan HAQIQIY ma'lumotlar bilan to'ldiradi."

    def handle(self, *args, **options):
        # Ensure base (untranslated) fields land in the default language (uz).
        translation.activate("uz")
        self._clear()
        self._siteconfig()
        self._sitecopy()
        self._about()
        self._stats()
        self._whyus()
        self._courses()
        self._teachers()
        self._testimonials()
        self._news()
        self._certificates()
        self._gallery()
        self.stdout.write(self.style.SUCCESS("Haqiqiy ma'lumotlar yuklandi."))

    def _clear(self):
        for model in (GalleryImage, GalleryVideo, GalleryAlbum, Course, CourseCategory,
                      Teacher, NewsPost, Certificate, Testimonial, WhyUsItem, StatItem,
                      AboutSection, SocialLink):
            model.objects.all().delete()

    # ---------------------------------------------------------------- config
    def _siteconfig(self):
        s = SiteConfig.get_solo()
        s.site_name = "Hope School"
        s.tagline = ("Bogʻiturkon va Romitandagi zamonaviy oʻquv markazi — ingliz tili, "
                     "matematika, kimyo, biologiya va tarix fanlaridan sertifikatga tayyorlov.")
        s.site_domain = "hopeschool.uz"
        s.phone_primary = "+998 99 979 52 39"
        s.phone_secondary = "+998 94 813 53 93"
        s.email = ""
        s.address = ("Buxoro viloyati, Romitan tumani, Bogʻiturkon qishlogʻi "
                     "(kollej yonida, apteka roʻparasida)")
        s.working_hours = "Dush–Yak, 09:00–20:00"
        s.latitude = "40.001100"
        s.longitude = "64.379700"
        s.seo_title = ("Hope School — Bogʻiturkon, Romitan | Ingliz tili, matematika, "
                       "kimyo, biologiya, tarix")
        s.seo_description = ("Bogʻiturkon va Romitandagi Hope School oʻquv markazi. Ingliz tilidan "
                             "CEFR, Multi-level (B2/C1) va IELTS sertifikatlariga tayyorlov; "
                             "matematika, kimyo, biologiya va tarix fanlari. 38+ oʻquvchimiz til "
                             "sertifikatiga erishgan. Birinchi 3 dars bepul.")
        s.save()

        SocialLink.objects.create(platform="telegram", label="Telegram kanal",
                                  url=CHANNEL, order=0)
        SocialLink.objects.create(platform="telegram_group", label="Telegram guruh",
                                  url="https://t.me/hope_school_group", order=1)

    def _sitecopy(self):
        c = SiteCopy.get_solo()
        c.results_eyebrow = "Natijalar"
        c.results_title = "Oʻquvchilarimiz natijalari"
        c.results_link_label = "Barcha natijalar"
        # Real quotes from our own channel (not parent reviews) — see _testimonials.
        c.testimonials_title = "Hope School kanalidan"
        c.save()

    # ------------------------------------------------------------- about/why
    def _about(self):
        a = AboutSection(
            subtitle="Biz haqimizda",
            title="Bilim — ishonch — natija",
            body=(
                "<p>Hope School (avvalgi nomi — Hope Academy) Buxoro viloyati, Romitan tumani "
                "Bogʻiturkon qishlogʻida 2023-yildan faoliyat yuritadi. Markazning Bogʻiturkon va "
                "Romitanda ikki filiali bor.</p>"
                "<p>Asosiy yoʻnalishimiz — ingliz tili. Darslarni 2×C1 darajali oʻqituvchi "
                "Umid Abdurahmonov olib boradi va oʻquvchilarni 0 dan boshlab CEFR, Multi-level "
                "(B2/C1) hamda IELTS sertifikatlariga tayyorlaydi. Shuningdek matematika, kimyo, "
                "biologiya va tarix fanlaridan ham guruhlar mavjud.</p>"
                "<p>Kichik guruhlar (13–15 oʻquvchi), haftalik va oylik testlar, mock imtihonlar "
                "va ota-onalar bilan doimiy aloqa — natijaga yoʻnaltirilgan metodikamiz shu. "
                "Bugungacha 38 dan ortiq oʻquvchimiz B2/IELTS sertifikatiga erishgan, "
                "oʻquvchilarimiz Prezident va ixtisoslashtirilgan maktablarga, akademik litseyga "
                "qabul qilingan, viloyat olimpiadasida gʻolib boʻlgan.</p>"
                "<p>Birinchi 3 ta sinov darsi bepul — keling, bilim darajangizni aniqlaymiz va "
                "sizga mos guruhni tanlaymiz.</p>"
            ),
            order=1,
        )
        a.image.save(*load_img("about/about-classroom.jpg"), save=False)
        a.save()

    def _stats(self):
        data = [
            (38, "+", "Sertifikat sohibi oʻquvchi", True),
            (5, "", "Fan yoʻnalishi", False),
            (2, "", "Filial: Bogʻiturkon, Romitan", False),
            (3, "+", "Yillik tajriba (2023-yildan)", False),
        ]
        for i, (n, suf, label, accent) in enumerate(data):
            StatItem.objects.create(number=n, suffix=suf, label=label, accent=accent, order=i)

    def _whyus(self):
        data = [
            ("Natijaga yoʻnaltirilgan taʼlim",
             "38 dan ortiq oʻquvchimiz B2/IELTS sertifikatiga erishdi.", "chart", True),
            ("2×C1 darajali ustoz",
             "Ingliz tili darslarini 2×C1 sertifikatli Umid Abdurahmonov olib boradi.", "users", False),
            ("Kichik guruhlar",
             "Har guruhda 13–15 oʻquvchi — har bir bolaga eʼtibor.", "group", False),
            ("Doimiy nazorat",
             "Haftalik va oylik testlar, mock imtihonlar, ota-onalar guruhi.", "method", False),
        ]
        for i, (t, d, ic, accent) in enumerate(data):
            WhyUsItem.objects.create(title=t, description=d, icon=ic, accent=accent, order=i)

    # ----------------------------------------------------------------- courses
    def _courses(self):
        til = CourseCategory.objects.create(name="Til", slug="til", order=0)
        aniq = CourseCategory.objects.create(name="Aniq fan", slug="aniq-fan", order=1)
        tabiiy = CourseCategory.objects.create(name="Tabiiy fan", slug="tabiiy-fan", order=2)
        ijtimoiy = CourseCategory.objects.create(name="Ijtimoiy fan", slug="ijtimoiy-fan", order=3)

        Course.objects.create(
            category=til, name="Ingliz tili", slug="ingliz-tili",
            short_description="0 dan B2/C1 gacha — CEFR, Multi-level va IELTS sertifikatlariga tayyorlov.",
            description=(
                "<p>Asosiy yoʻnalishimiz. Darslarni 2×C1 darajali Umid Abdurahmonov olib boradi.</p>"
                "<ul>"
                "<li>Darajalar: Starter (0 dan) → Elementary → Intermediate (B1) → B2/C1;</li>"
                "<li>CEFR / Multi-level va IELTS imtihoniga tayyorlov;</li>"
                "<li>“Bolajon” guruhi — 2–5-sinf oʻquvchilari uchun qiziqarli ingliz tili;</li>"
                "<li>Prezident va ixtisoslashtirilgan maktablarga, akademik litseyga tayyorlov;</li>"
                "<li>Haftada 3 kun, haftalik va oylik testlar, mock imtihonlar, “Movie time”.</li>"
                "</ul>"
                "<p>Oylik toʻlov 250 000 soʻmdan; Multi-level kuchaytirilgan kurs — 300 000 soʻm. "
                "Guruhda 13–15 oʻquvchi. Birinchi 3 ta sinov darsi bepul.</p>"
            ),
            duration_text="Doimiy qabul", group_size="13–15",
            price=250000, price_note="soʻm/oy", is_price_visible=True,
            icon="language", is_featured=True, order=0,
        )
        Course.objects.create(
            category=aniq, name="Matematika", slug="matematika",
            short_description="0 dan — Prezident, Al-Xorazmiy maktablari va DTM blokiga tayyorlov.",
            description=(
                "<p>Oʻqituvchi: Axadova G. 1–4, 5–8 va 9–10-sinflar uchun guruhlar.</p>"
                "<ul>"
                "<li>0 dan boshlangʻich tayyorlov;</li>"
                "<li>Prezident va Al-Xorazmiy ixtisoslashtirilgan maktablariga tayyorlov;</li>"
                "<li>Abituriyentlar uchun DTM majburiy blok;</li>"
                "<li>Dush/Chor/Juma 15:00–17:00, haftalik va oylik testlar.</li>"
                "</ul>"
                "<p>Oylik toʻlov 200 000 soʻmdan. Guruhda 13–15 oʻquvchi.</p>"
            ),
            duration_text="Doimiy qabul", group_size="13–15",
            price=200000, price_note="soʻm/oy", is_price_visible=True,
            icon="calc", is_featured=True, order=1,
        )
        Course.objects.create(
            category=tabiiy, name="Kimyo", slug="kimyo",
            short_description="Maktab dasturi va imtihonlarga puxta tayyorgarlik.",
            description=(
                "<p>Amaliy mashgʻulotlar va masalalar yechish orqali chuqur oʻzlashtirish.</p>"
                "<p>Sesh/Pay/Shan 15:00–18:00. Oylik toʻlov 250 000 soʻm.</p>"
            ),
            duration_text="Doimiy qabul", group_size="13–15",
            price=250000, price_note="soʻm/oy", is_price_visible=True,
            icon="method", order=2,
        )
        Course.objects.create(
            category=tabiiy, name="Biologiya", slug="biologiya",
            short_description="Maktab va imtihonlarga tayyorlov.",
            description=(
                "<p>Mavzularni tushunarli, qiziqarli va tizimli oʻrganish.</p>"
                "<p>Dush/Chor/Juma 15:00–18:00. Oylik toʻlov 250 000 soʻm.</p>"
            ),
            duration_text="Doimiy qabul", group_size="13–15",
            price=250000, price_note="soʻm/oy", is_price_visible=True,
            icon="star", order=3,
        )
        Course.objects.create(
            category=ijtimoiy, name="Tarix", slug="tarix",
            short_description="Asosiy blok, majburiy fan va sertifikatga tayyorlov.",
            description=(
                "<p>Oʻqituvchi: Murtazoyev Sherzod (A+ sertifikat sohibi).</p>"
                "<ul><li>Asosiy blok;</li><li>Majburiy fanlar;</li>"
                "<li>Sertifikatga tayyorlov.</li></ul>"
                "<p>Birinchi 3 ta sinov darsi bepul.</p>"
            ),
            duration_text="Doimiy qabul", group_size="13–15",
            is_price_visible=False, icon="book", order=4,
        )

    # ---------------------------------------------------------------- teachers
    def _teachers(self):
        Teacher.objects.create(
            full_name="Umid Abdurahmonov", slug="umid-abdurahmonov",
            position="Asoschi · Ingliz tili oʻqituvchisi · 2×C1",
            subjects="Ingliz tili",
            bio=("<p>Hope School asoschisi va bosh ingliz tili oʻqituvchisi. 2×C1 darajaga ega "
                 "(Listening/Reading 75, overall 65). 2023-yildan beri oʻquvchilarni CEFR, "
                 "Multi-level (B2/C1) va IELTS sertifikatlariga tayyorlaydi — 38 dan ortiq "
                 "oʻquvchisi til sertifikatiga erishgan.</p>"),
            telegram_url="https://t.me/Abdurakhmonov_Umid", order=0,
        )
        Teacher.objects.create(
            full_name="Axadova G.", slug="axadova-g",
            position="Matematika oʻqituvchisi", subjects="Matematika",
            bio=("<p>Matematika oʻqituvchisi. Prezident va ixtisoslashtirilgan maktablarga "
                 "tayyorlov guruhlarini olib boradi.</p>"),
            order=1,
        )
        Teacher.objects.create(
            full_name="Murtazoyev Sherzod", slug="murtazoyev-sherzod",
            position="Tarix oʻqituvchisi · A+ sertifikat", subjects="Tarix",
            bio=("<p>Tarix oʻqituvchisi, A+ sertifikat sohibi. Asosiy blok, majburiy fan va "
                 "sertifikatga tayyorlov kurslarini olib boradi.</p>"),
            order=2,
        )

    # ------------------------------------------------------------ testimonials
    def _testimonials(self):
        """Real quotes published on our own Telegram channel (not parent reviews)."""
        data = [
            ("Hope School", "Telegram kanalidan",
             "Bilim — bu sizni butun umr boʻyi oziqlantiradigan boylik. Oʻzingizga sarmoya "
             "qilishdan qoʻrqmang."),
            ("Hope School", "Telegram kanalidan",
             "Oʻqish — bu izlanish, kamolotga erishish uchun oʻz ustida tinmasdan qilingan "
             "mehnat. Oʻqish — bu sabr va oxirida shirin natija!"),
            ("Umid Abdurahmonov", "Ingliz tili oʻqituvchisi",
             "Men va jamoam sizga B2/C1 natija olishingizga maksimal yordam beramiz. "
             "Maqsadli reja va tajribali ustozlardan berilgan bilim uchun kafolat beramiz."),
            ("Hope School", "Telegram kanalidan",
             "Qiyinchiliklar oʻtadi, gʻalaba va ilm esa siz bilan qoladigan tuhfa. Qilingan "
             "harakat va natijalar qoladi."),
        ]
        for i, (name, role, content) in enumerate(data):
            Testimonial.objects.create(author_name=name, author_role=role, content=content,
                                       order=i)

    # ----------------------------------------------------------------- news
    def _news(self):
        def aware(y, m, d, hh=12, mm=0):
            return timezone.make_aware(datetime(y, m, d, hh, mm))

        items = [
            ("Ingliz tilidan yangi 0 dan guruh", "ingliz-tili-yangi-guruh-2026",
             "Qabul", True, aware(2026, 2, 2),
             "7-fevraldan ingliz tilidan 0 dan (beginner) yangi guruh shakllanmoqda. Birinchi "
             "3 ta dars bepul.",
             "<p>“Hope School” oʻquv markazida 7-fevraldan ingliz tilidan 0 dan (beginner) yangi "
             "guruh shakllantirilmoqda.</p><ul>"
             "<li>Haftada 3 kun (Dush, Chor, Jum);</li>"
             "<li>CEFR/IELTS sertifikati va Prezident maktablariga tayyorlovning poydevori;</li>"
             "<li>Har haftalik testlar va ota-onalar guruhi orqali doimiy nazorat;</li>"
             "<li>Oʻqituvchi: Umid Abdurahmonov (2×C1);</li>"
             "<li>Kurs toʻlovi: 250 000 soʻm. Birinchi 3 ta sinov darsi bepul.</li></ul>"
             "<p>Yozilish: @Abdurakhmonov_Umid · +998 99 979 52 39</p>"),

            ("2026-yilning birinchi “Bolajon” guruhi", "bolajon-guruhi-2026",
             "Yangilik", False, aware(2026, 2, 9),
             "2–4-sinf oʻquvchilari uchun qiziqarli ingliz tili guruhi boshlanmoqda.",
             "<p>“Hope School”da 2026-yil uchun birinchi “Bolajon” ingliz tili guruhi "
             "boshlanmoqda — 2-sinfdan 4-sinfgacha oʻquvchilar uchun.</p><ul>"
             "<li>Ingliz tilini qiziqarli oʻyinlar orqali oʻrgatish;</li>"
             "<li>Har darsda baholash tizimi orqali ragʻbatlantirish;</li>"
             "<li>Har haftalik testlar va mashqlar; ota-onalarga darsdan video parcha;</li>"
             "<li>Olimpiadalar va nufuzli maktablarga tayyorlov.</li></ul>"
             "<p>Birinchi 3 ta sinov darsi bepul.</p>"),

            ("Saidov Samadbek — viloyat olimpiadasi gʻolibi", "olimpiada-galaba-samadbek",
             "Yutuq", True, aware(2025, 12, 7),
             "5-sinf oʻquvchimiz ingliz tili fanidan tuman va viloyat olimpiadasida 1-oʻrinni egalladi.",
             "<p>5-sinf oʻquvchimiz Saidov Samadbek ingliz tili fanidan viloyat olimpiadasida "
             "1-oʻrinni egalladi. Romitan tumanida ham 1-oʻrinni qoʻlga kiritgan oʻquvchimiz endi "
             "Respublika bosqichiga yoʻl oldi.</p>"
             "<p>Toʻgʻri tanlangan metod, oʻquvchining harakatchanligi va ota-onaning eʼtibori "
             "bilan erishilgan natija. Oila aʼzolarini tabriklaymiz!</p>"),

            ("Rayimov Sunnatbek akademik litseyga qabul qilindi", "litsey-qabul-sunnatbek",
             "Yutuq", False, aware(2025, 9, 8),
             "Oʻquvchimiz faqat ingliz tilini puxta oʻrganish orqali IIV Buxoro akademik litseyiga qabul qilindi.",
             "<p>“Hope School” oʻquvchisi Rayimov Sunnatbek Ichki Ishlar Vazirligi Buxoro "
             "akademik litseyiga qabul qilindi. Boshqa fanlardan kurs olmasdan, faqat ingliz "
             "tilini puxta oʻrganish orqali erishilgan natija. Tabriklaymiz!</p>"
             "<p>Harbiy va akademik litseyga tayyorlov kurslarimizga qabul davom etmoqda.</p>"),

            ("Tarix fanidan yangi oʻqituvchi", "tarix-oqituvchi-murtazoyev",
             "Jamoa", False, aware(2025, 11, 14),
             "Jamoamizga A+ sertifikatli tarix oʻqituvchisi Murtazoyev Sherzod qoʻshildi.",
             "<p>“Hope School” jamoasiga A+ sertifikat sohibi, tarix oʻqituvchisi Murtazoyev "
             "Sherzod qoʻshildi. Tarix fanidan asosiy blok, majburiy fanlar va sertifikatga "
             "tayyorlov kurslariga “start” beramiz.</p>"
             "<p>Birinchi 3 ta sinov darsi mutlaqo bepul.</p>"),

            ("Aprel–May Multi-level mock imtihonlari", "mock-aprel-may-2026",
             "Tadbir", False, aware(2026, 4, 13),
             "Aprel va May oylarida imtihon topshiradigan guruhlar uchun Listening + Reading mock testlari oʻtkazilmoqda.",
             "<p>Ingliz tili fanidan Aprel va May oylarida Multi-level imtihoni topshiradigan "
             "guruhlar bilan Eshitish (Listening) va Oʻqish (Reading) koʻnikmasini aniqlovchi "
             "mock testlar muntazam oʻtkazilmoqda.</p>"
             "<p>Har bir testdan soʻng xatolar ustida chuqur tahlil qilinadi.</p>"),
        ]
        for (title, slug, badge, accent, dt, excerpt, body) in items:
            NewsPost.objects.create(
                title=title, slug=slug, badge=badge, badge_accent=accent,
                excerpt=excerpt, body=body, published_at=dt,
                is_featured=accent,
            )

    # ------------------------------------------------------------ certificates
    def _certificates(self):
        # (student, badge, accent, score/description, channel post id)
        # NOTE: badge "B2"/"IELTS"/"C1" is used ONLY where the channel post (or the
        # Dec-2025 master list #134/#65) explicitly states the level. The most recent
        # Apr-2026 result posts give only Listening/Reading scores ("Ingliz tili blok
        # yopildi") without naming a level, so they carry the neutral badge "Natija" —
        # the owner can upgrade them to B2/C1 in admin once confirmed.
        data = [
            ("Axtamov Jahongir", "Natija", True, "Listening 63 · Reading 75 — eng yuqori natija", 173),
            ("Mansurova Mashhura", "IELTS", True, "IELTS 6.5 — Reading 6.5 · Listening 6.5", 28),
            ("Baxshillayev Ulugʻbek", "B2 · 2x", True, "Reading 75 — C1 ga bir qadam", 182),
            ("Saidov Samadbek", "Olimpiada", True, "Viloyat ingliz tili olimpiadasi — 1-oʻrin (5-sinf)", 122),
            ("Rayimov Sunnatbek", "Litsey", True, "IIV Buxoro akademik litseyiga qabul — faqat ingliz tili bilan", 73),
            ("Jahongirov Samirbek", "Maktab", True, "al-Xorazmiy, Kogon, Galaosiyo — 3 ta ixtisoslashtirilgan maktab (6-sinf)", 80),
            ("Samadova Sabrina", "B2", True, "Markazning birinchi sertifikati — CEFR 55 (2023)", 26),
            ("Shuxratova Zahrobegim", "B2 · 2x", False, "Listening 54 · Reading 65", 153),
            ("Ergasheva Nigora", "B2", False, "Listening 56 · Reading 64", 155),
            ("Nusratova Madinabonu", "Natija", False, "Listening 55 · Reading 63 — ingliz tili bloki yakunlandi", 172),
            ("Obloqulov Artur", "B2", False, "Listening 54 · Reading 62", 156),
            ("Umid Abdurahmonov", "C1", True, "Ustoz natijasi — 2×C1 · Reading 75 · overall 65", 50),
            ("Joʻrayeva Charos", "Natija", False, "Listening 54 · Reading 61 — ingliz tili bloki yakunlandi", 171),
            ("Akramov Abdulatif", "Natija", False, "Reading 61 — ingliz tili bloki yakunlandi", 170),
            ("Shuxratova Shahruza", "B2", False, "Listening 53 · Reading 64", 151),
            ("Axmetova Leyla", "B2", False, "Listening 54 · Reading 59", 152),
            ("Baxshilloyeva Mushtariybonu", "B2", False, "Listening 54 · Reading 57", 154),
            ("Mirmurotova Tabassum", "B2 · 2x", False, "11-sinf — Aprel va Mayda 2 marta B2", 59),
            ("Sattorov Abdusattor", "B2 · 2x", False, "8-sinf oʻquvchisi", 109),
            ("Hakimova Parvina", "B2", False, "9-sinf oʻquvchisi", 105),
            ("Azimov Amin", "B2 · 2x", False, "Overall 54", 45),
            ("Mahmudova Ruhshona", "B2", False, "53 ball", 58),
            ("Nasriddinov Mahmudjon", "Maktab", False, "al-Xorazmiy (45.7), Kogon — 6-sinf", 82),
            ("Abduqodirov Bekzod", "Maktab", False, "Qorakoʻl xalqaro ixtisoslashtirilgan maktab — 5-sinf", 83),
        ]
        for i, (name, badge, accent, desc, post_id) in enumerate(data):
            Certificate.objects.create(
                title=f"{name} — {badge}", student_name=name, description=desc,
                badge=badge, badge_accent=accent,
                external_url=f"{CHANNEL}/{post_id}", order=i,
            )

    # ------------------------------------------------------------- gallery
    def _gallery(self):
        album = GalleryAlbum.objects.create(title="Oʻquv jarayoni", slug="oquv-jarayoni", order=0)
        photos = [
            ("gallery/01-ingliz-tili-sinfxonasi.jpg", "Ingliz tili sinfxonasi"),
            ("gallery/02-london-mural-sinf.jpg", "London uslubidagi sinfxona"),
            ("gallery/03-yozma-ish-jarayoni.jpg", "Yozma ish jarayoni"),
            ("gallery/04-bolajon-haftalik-test.jpg", "“Bolajon” guruhi — haftalik test"),
            ("gallery/05-online-mock-test.jpg", "Online mock test"),
            ("gallery/06-imtihonga-tayyorgarlik.jpg", "Imtihonga tayyorgarlik"),
        ]
        for i, (relpath, caption) in enumerate(photos):
            gi = GalleryImage(album=album, caption=caption,
                              alt_text=f"Hope School — {caption}", order=i)
            gi.image.save(*load_img(relpath), save=False)
            gi.save()
