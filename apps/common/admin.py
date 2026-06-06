from django.contrib import admin
from django.contrib.auth.models import Group

# Kichik marketing sayt uchun Group modeli kerak emas — admindan olib tashlaymiz.
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass
