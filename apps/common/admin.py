from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.decorators import action
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.common.translation import fill_translations_bulk, missing_translation_fields

# Kichik marketing sayt uchun Group modeli kerak emas — admindan olib tashlaymiz.
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


# ---------------------------------------------------------------------------
# Foydalanuvchilar (xodimlar) — admindan qoʻshish/oʻchirish
# ---------------------------------------------------------------------------
# Standart Django UserAdmin'i Unfold uslubisiz koʻrinadi, shuningdek admin
# orqali superuser yaratish/berish imkonini ochiq qoldiradi. Quyidagi versiya:
#   * Unfold uslubi (form/add_form/change_password_form unfold.forms'dan);
#   * `is_superuser` har doim faqat-oʻqish — admin orqali yangi superuser
#     yaratib yoki mavjud hisobga superuser huquqini berib boʻlmaydi
#     (birinchi superuser CLI `createsuperuser` orqali yaratiladi);
#   * superuserlar bir-birini himoyalangan: boshqa superuserning parolini
#     oʻzgartirib, oʻchirib yoki huquqlarini (faollik/xodimlik) oʻzgartirib
#     boʻlmaydi;
#   * oddiy (superuser boʻlmagan) adminlar huquq maydonlariga tegolmaydi —
#     imtiyozni oshirib boʻlmaydi.
# Group bu loyihada ishlatilmaydi (yuqorida unregister qilingan), shuning uchun
# huquqlar to'plamiga `groups` ham kiritilgan (himoya uchun, zarar qilmaydi).
_PERMISSION_FIELDS = ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Unfold-styled auth forms.
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ("username", "email", "first_name", "last_name",
                    "is_staff", "is_superuser", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")

    def _is_other_superuser(self, request, obj):
        """obj — request.user'dan boshqa superuser'mi?"""
        return obj is not None and obj.is_superuser and obj.pk != request.user.pk

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # `is_superuser` admin orqali HECH QACHON oʻzgartirilmaydi → yangi
        # superuser yaratib/berib boʻlmaydi. (readonly maydon formadan butunlay
        # chiqarib tashlanadi, shuning uchun soxta POST ham huquq berolmaydi.)
        # Superuser boʻlmagan admin yoki boshqa superuserni tahrirlash holatida
        # butun huquqlar bloki qulflanadi.
        if not request.user.is_superuser or self._is_other_superuser(request, obj):
            for field in _PERMISSION_FIELDS:
                if field not in readonly:
                    readonly.append(field)
        elif "is_superuser" not in readonly:
            readonly.append("is_superuser")
        return tuple(readonly)

    def has_delete_permission(self, request, obj=None):
        # Boshqa superuserni oʻchirib boʻlmaydi (yakka, change-form va bulk
        # `delete_selected` — barchasi shu nuqtadan oʻtadi: bulk yoʻli
        # get_deleted_objects() ichida har bir obyekt uchun shuni chaqiradi).
        if self._is_other_superuser(request, obj):
            return False
        return super().has_delete_permission(request, obj)

    def user_change_password(self, request, id, form_url=""):
        # Boshqa superuserning parolini oʻzgartirib boʻlmaydi.
        user = self.get_object(request, unquote(id))
        if self._is_other_superuser(request, user):
            raise PermissionDenied
        return super().user_change_password(request, id, form_url)


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
