from django.views.generic import DetailView, ListView

from .models import NewsPost


class NewsListView(ListView):
    template_name = "news/list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return NewsPost.objects.filter(is_published=True)


class NewsDetailView(DetailView):
    template_name = "news/detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return NewsPost.objects.filter(is_published=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["related"] = (
            NewsPost.objects.filter(is_published=True)
            .exclude(pk=self.object.pk)[:3]
        )
        return ctx
