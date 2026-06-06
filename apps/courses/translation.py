from modeltranslation.translator import TranslationOptions, register

from .models import Course, CourseCategory


@register(CourseCategory)
class CourseCategoryTR(TranslationOptions):
    fields = ("name",)


@register(Course)
class CourseTR(TranslationOptions):
    fields = ("name", "short_description", "description", "duration_text",
              "price_note", "meta_title", "meta_description")
