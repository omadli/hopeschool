import threading

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Lead
from .notifications import notify_new_lead


@receiver(post_save, sender=Lead, dispatch_uid="leads_notify_new_lead")
def lead_created(sender, instance, created, **kwargs):
    """On a new lead, fire the Telegram notification after the DB commits.

    Runs in a daemon thread so the HTTP request to Telegram never delays or
    breaks the user's submission. This is the single place a thread is spawned.
    """
    if not created:
        return

    def _dispatch():
        threading.Thread(
            target=notify_new_lead, args=(instance,), daemon=True
        ).start()

    transaction.on_commit(_dispatch)
