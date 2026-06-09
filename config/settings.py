"""
Django settings for Hope School.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ["*"]),
    SECRET_KEY=(str, "django-insecure-dev-key-change-me"),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Telegram (lead notifications) — filled in later phases
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_ADMIN_CHAT_ID = env("TELEGRAM_ADMIN_CHAT_ID", default="")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Unfold admin theme — MUST precede django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",

    # i18n — MUST precede django.contrib.admin
    "modeltranslation",

    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # Third-party
    "solo",
    "django_tailwind_cli",
    "django_ckeditor_5",
    "easy_thumbnails",

    # Local apps
    "apps.common",
    "apps.siteconfig",
    "apps.pages",
    "apps.courses",
    "apps.teachers",
    "apps.gallery",
    "apps.testimonials",
    "apps.news",
    "apps.certificates",
    "apps.leads",
    "apps.analytics",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",   # after Session, before Common (i18n_patterns)
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.analytics.middleware.VisitLogMiddleware",  # last: log public page visits
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.common.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database (SQLite + WAL for safer concurrent analytics writes)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "init_command": (
                "PRAGMA journal_mode=WAL;"
                "PRAGMA synchronous=NORMAL;"
                "PRAGMA foreign_keys=ON;"
                "PRAGMA busy_timeout=5000;"
            ),
            "transaction_mode": "IMMEDIATE",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization (uz default, ru, en)
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "uz"
LANGUAGES = [
    ("uz", "Oʻzbekcha"),
    ("ru", "Русский"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "Asia/Tashkent"

MODELTRANSLATION_DEFAULT_LANGUAGE = "uz"
MODELTRANSLATION_LANGUAGES = ("uz", "ru", "en")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("uz", "ru", "en")
MODELTRANSLATION_CUSTOM_FIELDS = ("CKEditor5Field",)

# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "assets", BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# easy-thumbnails — responsive WebP delivery (Core Web Vitals)
# ---------------------------------------------------------------------------
# Default quality for generated thumbnails. 82 is a good quality/size
# sweet spot for photographic content. THUMBNAIL_QUALITY backs the
# thumbnailer's per-instance default; DEFAULT_OPTIONS covers the tag path.
THUMBNAIL_DEFAULT_OPTIONS = {"quality": 82}
THUMBNAIL_QUALITY = 82
# Keep the original extension for the <img> fallback (JPG stays JPG, PNG stays
# PNG, etc.). The WebP <source> variants force a .webp extension explicitly in
# apps/common/templatetags/media_tags.py (PRESERVE_EXTENSIONS alone keeps the
# source extension even for format="WEBP", which would mislabel the file).
THUMBNAIL_PRESERVE_EXTENSIONS = ("jpg", "jpeg", "png", "gif", "webp")
# Silent in production: a missing/unreadable source yields an empty URL
# (the template keeps its gradient placeholder) instead of raising.
THUMBNAIL_DEBUG = False

# Upload limits (security)
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024   # 12 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000

# CKEditor 5
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpg", "jpeg", "png", "webp", "gif"]
CKEDITOR_5_MAX_FILE_SIZE = 5  # MB
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "underline", "strikethrough", "code", "|",
            "fontSize", "fontColor", "highlight", "|",
            "alignment", "|",
            "bulletedList", "numberedList", "todoList", "outdent", "indent", "|",
            "link", "blockQuote", "insertImage", "mediaEmbed", "insertTable",
            "horizontalLine", "|",
            "removeFormat", "sourceEditing", "|",
            "undo", "redo",
        ],
        "height": "420px",
        "image": {
            "toolbar": ["imageTextAlternative", "|", "resizeImage"],
        },
        "table": {
            "contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"],
        },
        # Save the real <iframe> into the field HTML so embeds render on the site.
        "mediaEmbed": {"previewsInData": True},
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading2", "view": "h2", "title": "Sarlavha 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Sarlavha 3", "class": "ck-heading_heading3"},
                {"model": "heading4", "view": "h4", "title": "Sarlavha 4", "class": "ck-heading_heading4"},
            ],
        },
    },
}

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Tailwind CSS (standalone CLI, Tailwind v4 — no Node)
# ---------------------------------------------------------------------------
TAILWIND_CLI_VERSION = "4.1.3"
TAILWIND_CLI_SRC_CSS = "assets/css/source.css"
TAILWIND_CLI_DIST_CSS = "css/tailwind.css"
TAILWIND_CLI_AUTOMATIC_DOWNLOAD = True

# ---------------------------------------------------------------------------
# Unfold admin (expanded with dashboard/sidebar in later phases)
# ---------------------------------------------------------------------------
from django.templatetags.static import static  # noqa: E402
from django.urls import reverse_lazy  # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402

UNFOLD = {
    "SITE_TITLE": "Hope School",
    "SITE_HEADER": "Hope School",
    "SITE_SUBHEADER": _("Boshqaruv paneli"),
    "DASHBOARD_CALLBACK": "apps.analytics.dashboard.dashboard_callback",
    "SITE_SYMBOL": "school",
    "SITE_URL": "/",  # "Saytni koʻrish" tugmasi
    # Qo'shimcha admin CSS (CKEditor tungi rejim tuzatmasi + UI tweaks)
    "STYLES": [
        lambda request: static("css/admin_extra.css"),
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "COLORS": {
        "primary": {
            "50": "238 244 255",
            "100": "217 230 255",
            "200": "179 205 255",
            "300": "132 172 247",
            "400": "81 137 236",
            "500": "44 107 212",
            "600": "34 87 179",
            "700": "28 70 143",
            "800": "24 56 111",
            "900": "18 42 82",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": _("Boshqaruv"),
                "items": [
                    {"title": _("Bosh sahifa"), "icon": "dashboard", "link": reverse_lazy("admin:index")},
                    {"title": _("Saytni koʻrish"), "icon": "language", "link": "/"},
                ],
            },
            {
                "title": _("Sayt mazmuni"),
                "items": [
                    {"title": _("Kurslar"), "icon": "menu_book", "link": reverse_lazy("admin:courses_course_changelist")},
                    {"title": _("Oʻqituvchilar"), "icon": "groups", "link": reverse_lazy("admin:teachers_teacher_changelist")},
                    {"title": _("Yangiliklar"), "icon": "campaign", "link": reverse_lazy("admin:news_newspost_changelist")},
                    {"title": _("Galereya"), "icon": "photo_library", "link": reverse_lazy("admin:gallery_galleryalbum_changelist")},
                    {"title": _("Galereya videolari"), "icon": "smart_display", "link": reverse_lazy("admin:gallery_galleryvideo_changelist")},
                    {"title": _("Sertifikatlar"), "icon": "workspace_premium", "link": reverse_lazy("admin:certificates_certificate_changelist")},
                    {"title": _("Fikrlar"), "icon": "reviews", "link": reverse_lazy("admin:testimonials_testimonial_changelist")},
                ],
            },
            {
                "title": _("Bosh sahifa bloklari"),
                "items": [
                    {"title": _("Hero bo'limi"), "icon": "wallpaper", "link": reverse_lazy("admin:pages_herosection_changelist")},
                    {"title": _("Bosh sahifa videosi"), "icon": "smart_display", "link": reverse_lazy("admin:pages_homevideo_changelist")},
                    {"title": _("Biz haqimizda"), "icon": "article", "link": reverse_lazy("admin:pages_aboutsection_changelist")},
                    {"title": _("Statistika"), "icon": "bar_chart", "link": reverse_lazy("admin:pages_statitem_changelist")},
                    {"title": _("Nega biz"), "icon": "verified", "link": reverse_lazy("admin:pages_whyusitem_changelist")},
                    {"title": _("Sayt matnlari"), "icon": "edit_note", "link": reverse_lazy("admin:pages_sitecopy_changelist")},
                ],
            },
            {
                "title": _("Murojaatlar"),
                "items": [
                    {
                        "title": _("Arizalar"),
                        "icon": "inbox",
                        "link": reverse_lazy("admin:leads_lead_changelist"),
                        "badge": "apps.leads.badges.new_leads_count",
                    },
                ],
            },
            {
                "title": _("Analitika"),
                "items": [
                    {"title": _("Tashriflar"), "icon": "analytics", "link": reverse_lazy("admin:analytics_visitlog_changelist")},
                ],
            },
            {
                "title": _("Sozlamalar"),
                "items": [
                    {"title": _("Sayt sozlamalari"), "icon": "settings", "link": reverse_lazy("admin:siteconfig_siteconfig_changelist")},
                    {"title": _("Ijtimoiy tarmoqlar"), "icon": "share", "link": reverse_lazy("admin:siteconfig_sociallink_changelist")},
                    {"title": _("Foydalanuvchilar"), "icon": "person", "link": reverse_lazy("admin:auth_user_changelist")},
                ],
            },
        ],
    },
}
