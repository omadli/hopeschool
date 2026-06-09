from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from unfold.decorators import action

from apps.common.translation import fill_translations_bulk, missing_translation_fields

# Kichik marketing sayt uchun Group modeli kerak emas — admindan olib tashlaymiz.
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


@admin.action(description=_("UZ → RU/EN avto-tarjima (boʻsh maydonlarni toʻldirish)"))
def auto_translate_selected(modeladmin, request, queryset):
    """Bulk changelist action: fill empty target-language fields from UZ."""
    objs = fields = 0
    # Parallel + deduped: fan the per-field translation requests across a thread
    # pool instead of one blocking request-after-request (was minutes for a few
    # rows). Saves stay on the main thread.
    for obj, filled in fill_translations_bulk(list(queryset)):
        if filled:
            obj.save()
            objs += 1
            fields += filled
    if fields:
        messages.success(
            request,
            _("%(o)d ta yozuv, %(f)d ta maydon avto-tarjima qilindi. Iltimos, tekshiring.")
            % {"o": objs, "f": fields},
        )
    else:
        messages.info(request, _("Tanlangan yozuvlarda boʻsh tarjima maydoni topilmadi."))


class AutoTranslateAdminMixin:
    """Adds UZ → RU/EN machine-translation to any modeltranslation admin.

    Generic over every registered field, so it works on any model without
    per-model configuration:
      * a "UZ → RU/EN avto-tarjima" button on the change form's submit line
        (fills empty target fields from the UZ value, then the admin reviews
        and saves — matching "admin tekshirib saqlaydi");
      * the same as a bulk changelist action;
      * a save-time warning whenever a target translation is left empty, so
        translations are never silently half-done.

    Place FIRST in the admin base list so its ``save_model`` wraps Unfold's.
    """

    # Warn before navigating away from a change form with unsaved edits.
    warn_unsaved_form = True

    actions_submit_line = ("auto_translate_object",)

    @action(description=_("UZ → RU/EN avto-tarjima"), icon="translate")
    def auto_translate_object(self, request, obj):
        _, filled = fill_translations_bulk([obj])[0]
        if filled:
            obj.save()
            messages.success(
                request,
                _("Avto-tarjima: %(n)d ta maydon toʻldirildi. Tekshirib, saqlang.")
                % {"n": filled},
            )
        else:
            messages.info(request, _("Tarjima qilinadigan boʻsh maydon topilmadi."))

    def save_model(self, request, obj, form, change):
        # Unfold's save_model runs the submit-line action (which fills + saves
        # translations) inside super(), so by the time we inspect `obj` below the
        # auto-translated values are already present — no false warning.
        super().save_model(request, obj, form, change)
        missing = missing_translation_fields(obj)
        if missing:
            preview = ", ".join(missing[:6])
            more = _(" va boshqalar") if len(missing) > 6 else ""
            messages.warning(
                request,
                _("Tarjima toʻliq emas — boʻsh: %(fields)s%(more)s. "
                  "«UZ → RU/EN avto-tarjima» tugmasidan foydalaning.")
                % {"fields": preview, "more": more},
            )

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions["auto_translate_selected"] = (
            auto_translate_selected,
            "auto_translate_selected",
            auto_translate_selected.short_description,
        )
        return actions
