from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("author_name", "author_role", "rating", "is_featured", "is_active", "order")
    list_editable = ("is_featured", "is_active", "order")
    list_filter = ("is_featured", "is_active")
    search_fields = ("author_name", "content")
