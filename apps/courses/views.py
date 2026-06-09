from django.views.generic import DetailView

from .models import Course


class CourseDetailView(DetailView):
    template_name = "courses/detail.html"
    context_object_name = "course"

    def get_queryset(self):
        return (
            Course.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images")
        )
