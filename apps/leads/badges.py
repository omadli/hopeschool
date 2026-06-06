from .models import Lead


def new_leads_count(request):
    """Unfold sidebar badge: number of leads still in the 'new' state.

    Returns an empty string when there are none so no badge is shown.
    """
    count = Lead.objects.filter(status=Lead.Status.NEW).count()
    return str(count) if count else ""
