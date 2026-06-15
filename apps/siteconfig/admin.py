from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin
from solo.admin import SingletonModelAdmin
from unfold.admin import ModelAdmin

from apps.common.admin import AutoTranslateAdminMixin

from .models import SiteConfig, SocialLink, TelegramRecipient
from .widgets import LeafletLocationWidget


@admin.register(SocialLink)
class SocialLinkAdmin(ModelAdmin):
    list_display = ("__str__", "platform", "url", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("platform", "is_active")


@admin.register(TelegramRecipient)
class TelegramRecipientAdmin(ModelAdmin):
    list_display = ("__str__", "chat_id", "is_active")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    search_fields = ("name", "chat_id")


class SiteConfigForm(forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = "__all__"
        widgets = {
            "latitude": LeafletLocationWidget(),
        }


@admin.register(SiteConfig)
class SiteConfigAdmin(AutoTranslateAdminMixin, ModelAdmin, TabbedTranslationAdmin, SingletonModelAdmin):
    form = SiteConfigForm
    fieldsets = (
        (_("Brending"), {
            "fields": ("site_name", "tagline", "logo", "favicon", "site_domain"),
        }),
        (_("Kontaktlar"), {
            "fields": ("phone_primary", "phone_secondary", "email", "address", "working_hours"),
        }),
        (_("Joylashuv (xaritadan tanlang)"), {
            "fields": ("latitude", "longitude"),
            "description": _("Xaritani bosib yoki qidirib joylashuvni tanlang. "
                             "Google va Yandex xaritalari shu koordinatalardan avtomatik chiqadi."),
        }),
        (_("Xarita — qo‘lda override (ixtiyoriy)"), {
            "fields": ("google_maps_embed", "yandex_maps_embed"),
            "classes": ("collapse",),
            "description": _("Faqat maxsus embed kerak bo‘lsa to‘ldiring. Bo‘sh qoldirilsa, "
                             "yuqoridagi koordinatalardan foydalaniladi."),
        }),
        (_("SEO"), {
            "fields": ("seo_title", "seo_description", "og_image",
                       "google_site_verification", "yandex_verification", "bing_msvalidate"),
            "classes": ("collapse",),
        }),
        (_("Analitika"), {
            "fields": ("ga4_measurement_id", "yandex_metrica_id"),
            "classes": ("collapse",),
        }),
        (_("Telegram"), {
            "fields": ("telegram_notifications_enabled", "telegram_bot_token"),
            "classes": ("collapse",),
            "description": _("Bot tokenini kiriting, soʻng «Telegram qabul qiluvchilar» boʻlimida arizalarni qabul qiladigan adminlarni qoʻshing — bir nechta admin qoʻshish mumkin."),
        }),
    )
