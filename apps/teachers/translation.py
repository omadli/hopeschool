from modeltranslation.translator import TranslationOptions, register

from .models import Teacher


@register(Teacher)
class TeacherTR(TranslationOptions):
    fields = ("position", "bio", "subjects", "meta_title", "meta_description")
