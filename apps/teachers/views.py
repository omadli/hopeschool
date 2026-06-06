from django.views.generic import DetailView

from .models import Teacher


class TeacherDetailView(DetailView):
    template_name = "teachers/detail.html"
    context_object_name = "teacher"

    def get_queryset(self):
        return Teacher.objects.filter(is_active=True)
