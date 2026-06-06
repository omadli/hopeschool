import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from apps.certificates.models import Certificate
from apps.courses.models import Course, CourseCategory
from apps.gallery.models import GalleryAlbum, GalleryImage
from apps.news.models import NewsPost
from apps.pages.models import AboutSection, StatItem, WhyUsItem
from apps.siteconfig.models import SiteConfig
from apps.teachers.models import Teacher
from apps.testimonials.models import Testimonial


def gradient_tile(w, h, top, bottom):
    img = Image.new("RGB", (w, h), top)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = "Hope School uchun haqiqiy namunaviy ma'lumotlarni yuklaydi (eski demo tozalanadi)."

    def handle(self, *args, **options):
        self._clear()
        self._siteconfig()
        self._about()
        self._stats()
        self._whyus()
        self._courses()
        self._teachers()
        self._testimonials()
        self._news()
        self._certificates()
        self._gallery()
        self.stdout.write(self.style.SUCCESS("Demo ma'lumotlar yangilandi."))

    def _clear(self):
        for model in (GalleryImage, GalleryAlbum, Course, CourseCategory, Teacher,
                      NewsPost, Certificate, Testimonial, WhyUsItem, StatItem, AboutSection):
            model.objects.all().delete()

    def _siteconfig(self):
        s = SiteConfig.get_solo()
        s.site_name = "Hope School"
        s.tagline = ("Bogʻiturkon qishlogʻidagi zamonaviy oʻquv markazi — 0 dan boshlab "
                     "ingliz tili, matematika, kimyo va biologiya.")
        s.site_domain = "hopeschool.uz"
        s.phone_primary = "+998 99 979 52 39"
        s.phone_secondary = "+998 94 813 53 93"
        s.email = ""
        s.address = "Buxoro viloyati, Romitan tumani, Bogʻiturkon qishlogʻi"
        s.working_hours = "Dush–Shan, 09:00–18:00"
        s.latitude = "40.001100"
        s.longitude = "64.379700"
        s.telegram_url = "https://t.me/Hope_school_channel"
        s.telegram_group_url = "https://t.me/hope_school_group"
        s.seo_title = "Hope School — Bogʻiturkon, Romitan | Ingliz tili, matematika, kimyo, biologiya"
        s.seo_description = ("Bogʻiturkon qishlogʻidagi Hope School oʻquv markazi. 0 dan boshlab "
                             "ingliz tili, matematika, kimyo va biologiya boʻyicha milliy va xalqaro "
                             "sertifikatlarga tayyorlov.")
        s.save()

    def _about(self):
        AboutSection.objects.create(
            subtitle="Biz haqimizda",
            title="Bilim — ishonch — kelajak",
            body="Hope School (HOPE academy) — Bogʻiturkon qishlogʻidagi zamonaviy oʻquv markazi. "
                 "Biz oʻquvchilarni 0 dan boshlab ingliz tili, matematika, kimyo va biologiya "
                 "boʻyicha milliy va xalqaro sertifikatlarga tayyorlaymiz. Kichik guruhlar, tajribali "
                 "pedagoglar va natijaga yoʻnaltirilgan metodika.",
            order=1,
        )

    def _stats(self):
        data = [(300, "+", "Oʻquvchilar", False), (10, "+", "Oʻqituvchilar", False),
                (4, "", "Yoʻnalish", False), (98, "%", "Mamnunlik", True)]
        for i, (n, suf, label, accent) in enumerate(data):
            StatItem.objects.create(number=n, suffix=suf, label=label, accent=accent, order=i)

    def _whyus(self):
        data = [
            ("Natijaga yoʻnaltirilgan taʼlim", "Aniq maqsad — aniq natija.", "chart", False),
            ("Zamonaviy metodikalar", "Interaktiv va amaliyotga asoslangan darslar.", "method", False),
            ("Tajribali pedagoglar", "Milliy va xalqaro tajribaga ega ustozlar.", "users", True),
            ("Kichik guruhlar", "15 kishilik ixcham guruhlarda sifatli oʻrganish.", "group", True),
        ]
        for i, (t, d, ic, accent) in enumerate(data):
            WhyUsItem.objects.create(title=t, description=d, icon=ic, accent=accent, order=i)

    def _courses(self):
        til = CourseCategory.objects.create(name="Til", slug="til", order=0)
        aniq = CourseCategory.objects.create(name="Aniq fan", slug="aniq-fan", order=1)
        tabiiy = CourseCategory.objects.create(name="Tabiiy fan", slug="tabiiy-fan", order=2)
        data = [
            ("Ingliz tili", "ingliz-tili", til,
             "0 dan boshlab — milliy va xalqaro sertifikatlarga tayyorlov.",
             "Haftada 3 kun, 2 soatlik kuchaytirilgan darslar. Ikkita C1 oʻqituvchi doimiy nazorati. "
             "Birinchi 3 ta probniy dars bepul.",
             "Doimiy qabul", "15 kishi", "book", True),
            ("Matematika", "matematika", aniq,
             "0 dan boshlab — mantiqiy fikrlash va masala yechish.",
             "Haftada 3 kun (Dush/Chor/Juma 15:00), 2–2.5 soatlik darslar. Zamonaviy metodikalar va "
             "tajribali pedagog.",
             "Doimiy qabul", "Kichik guruh", "calc", True),
            ("Kimyo", "kimyo", tabiiy,
             "Maktab dasturi va imtihonlarga puxta tayyorgarlik.",
             "Amaliy mashgʻulotlar va masalalar yechish orqali chuqur oʻzlashtirish.",
             "Doimiy qabul", "Kichik guruh", "method", False),
            ("Biologiya", "biologiya", tabiiy,
             "Maktab va imtihonlarga tayyorlov.",
             "Mavzularni tushunarli, qiziqarli va tizimli oʻrganish.",
             "Doimiy qabul", "Kichik guruh", "star", False),
        ]
        for i, (name, slug, cat, short, desc, dur, grp, icon, feat) in enumerate(data):
            Course.objects.create(
                name=name, slug=slug, category=cat, short_description=short, description=desc,
                duration_text=dur, group_size=grp, icon=icon, is_featured=feat,
                is_price_visible=False, order=i,
            )

    def _teachers(self):
        data = [
            ("Axadova", "oqituvchi-axadova", "Matematika oʻqituvchisi · Tajribali pedagog", "Matematika", 8),
            ("Abdurahmonov U.", "oqituvchi-abdurahmonov", "Ingliz tili · C1 daraja", "Ingliz tili", 7),
            ("Karimova D.", "oqituvchi-karimova", "Kimyo oʻqituvchisi", "Kimyo", 6),
            ("Rahimov B.", "oqituvchi-rahimov", "Biologiya oʻqituvchisi", "Biologiya", 5),
        ]
        for i, (name, slug, pos, subj, exp) in enumerate(data):
            Teacher.objects.create(
                full_name=name, slug=slug, position=pos, subjects=subj, experience_years=exp,
                bio="Oʻz sohasining tajribali mutaxassisi, oʻquvchilarga gʻamxoʻrlik bilan yondashadi.",
                order=i,
            )

    def _testimonials(self):
        data = [
            ("Dildora opa", "Ona", "Farzandimning ingliz tili sezilarli darajada yaxshilandi. Ustozlar juda eʼtiborli."),
            ("Akmal aka", "Ota", "Matematikadan oʻgʻlim endi masalalarni mustaqil yecha oladi. Rahmat Hope School!"),
            ("Gulnoza opa", "Ona", "Kichik guruhlar va individual yondashuv haqiqatan ham natija beryapti."),
            ("Sardor aka", "Ota", "Markaz zamonaviy, ustozlar mehnatkash. Farzandim darslarga ishtiyoq bilan boradi."),
        ]
        for i, (name, role, content) in enumerate(data):
            Testimonial.objects.create(author_name=name, author_role=role, content=content, rating=5, order=i)

    def _news(self):
        now = timezone.now()
        items = [
            ("Yangi ingliz tili guruhi ochildi", "yangi-ingliz-tili-guruhi", "Eʼlon", True,
             "2-maydan soat 15:00–17:00 da 0 dan boshlab yangi ingliz tili guruhi ochiladi.",
             "Hope School oʻquv markazida 2-maydan soat 15:00–17:00 da yangi ingliz tili guruhi ochiladi. "
             "Darslar milliy va xalqaro sertifikatlarga tayyorlanishni xohlovchilar uchun 0 dan boshlab "
             "oʻtiladi.\n\n• Haftada 3 kun, 2 soatlik kuchaytirilgan darslar;\n"
             "• Ikkita C1 oʻqituvchi tomonidan doimiy nazorat;\n"
             "• 15 kishilik ixcham guruhlar;\n• Birinchi 3 ta probniy dars bepul.\n\n"
             "Yozilish uchun: +998 94 813 53 93"),
            ("Matematika kursi — 0 dan boshlab", "matematika-kursi-0-dan", "Yangilik", False,
             "Yangi matematika guruhi: haftada 3 kun (Dush/Chor/Juma 15:00), 2–2.5 soatlik darslar.",
             "Matematikani 0 dan boshlab oʻrganing! Zamonaviy metodikalar, tajribali pedagog va "
             "natijaga yoʻnaltirilgan taʼlim.\n\n• Dushanba, Chorshanba, Juma — 15:00;\n"
             "• 2–2.5 soatlik darslar;\n• Mantiqiy fikrlash va masala yechishga urgʻu.\n\n"
             "Maʼlumot uchun: +998 99 702 03 18"),
            ("Probniy birinchi 3 ta dars bepul", "probniy-darslar-bepul", "Aksiya", True,
             "Yangi oʻquvchilar uchun birinchi 3 ta dars mutlaqo bepul.",
             "Hope School da yangi oʻquvchilar uchun birinchi 3 ta probniy dars bepul. "
             "Bilim darajangizni aniqlaymiz va sizga mos guruhni tanlaymiz. Oʻrindiqlar soni cheklangan!"),
        ]
        for i, (title, slug, badge, accent, excerpt, body) in enumerate(items):
            NewsPost.objects.create(
                title=title, slug=slug, badge=badge, badge_accent=accent, excerpt=excerpt, body=body,
                published_at=now - timezone.timedelta(days=i * 5),
            )

    def _certificates(self):
        data = [
            ("Aziza R.", "IELTS Band 7.0", "IELTS", False),
            ("Bekzod T.", "Milliy sertifikat — Ingliz tili", "Milliy", True),
            ("Madina X.", "Kimyo olimpiadasi gʻolibi", "Gʻolib", True),
            ("Sardor M.", "Matematika — yuqori natija", "Matematika", False),
            ("Laylo A.", "Biologiya — milliy sertifikat", "Milliy", False),
        ]
        for i, (student, desc, badge, accent) in enumerate(data):
            Certificate.objects.create(
                title=f"{student} — {badge}", student_name=student, description=desc,
                badge=badge, badge_accent=accent, external_url="https://t.me/Hope_school_channel", order=i,
            )

    def _gallery(self):
        album = GalleryAlbum.objects.create(title="Oʻquv jarayoni", slug="oquv-jarayoni", order=0)
        palette = [((61, 127, 230), (28, 70, 143)), ((90, 150, 240), (34, 87, 179)),
                   ((120, 170, 245), (44, 107, 212)), ((61, 127, 230), (18, 42, 82)),
                   ((100, 160, 235), (24, 56, 111)), ((140, 180, 248), (28, 70, 143))]
        for i, (top, bottom) in enumerate(palette):
            gi = GalleryImage(album=album, caption=f"Lavha {i + 1}",
                              alt_text="Hope School oʻquv jarayoni", order=i)
            gi.image.save(f"demo-{i + 1}.jpg", gradient_tile(800, 600, top, bottom), save=False)
            gi.save()
