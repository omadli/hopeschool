"""Admin-login brute-force protection (django-axes).

The admin login is the only authentication surface. These tests assert the
app-level defence: failed attempts are recorded (audit trail) and a targeted
(IP + username) brute-force is locked out after AXES_FAILURE_LIMIT tries — even
if the correct password is finally supplied. See the AXES_* block in
config/settings.py.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()

# DEBUG=False under the test runner selects the WhiteNoise manifest storage,
# which needs a collectstatic manifest; swap in plain storage (mirrors the
# other admin tests) so rendering the login page never errors.
_PLAIN_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=_PLAIN_STORAGE, AXES_ENABLED=True)
class AdminLoginLockoutTests(TestCase):
    def setUp(self):
        self.password = "S3curePass!23"
        User.objects.create_superuser("boss", "boss@test.com", self.password)
        self.login_url = reverse("admin:login")

    def _attempt(self, password):
        return self.client.post(
            self.login_url,
            {"username": "boss", "password": password, "next": reverse("admin:index")},
        )

    def test_failed_attempt_is_recorded(self):
        """Every failed login is written to AccessAttempt (visible in admin)."""
        from axes.models import AccessAttempt
        self._attempt("wrong")
        self.assertEqual(AccessAttempt.objects.filter(username="boss").count(), 1)

    def test_lockout_after_five_failures_blocks_even_correct_password(self):
        for _ in range(5):
            self._attempt("wrong")
        # The 6th request is refused by axes before the password is checked.
        resp = self._attempt(self.password)
        self.assertEqual(resp.status_code, 429)

    def test_login_works_before_the_limit(self):
        """A correct password within the limit still logs in (no false lockout)."""
        resp = self._attempt(self.password)
        self.assertEqual(resp.status_code, 302)  # redirect to admin index
        self.assertRedirects(resp, reverse("admin:index"), fetch_redirect_response=False)
