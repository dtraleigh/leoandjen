from datetime import date
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

from data.models import AuthToken, SolarEnergy

COMMAND = "data.management.commands.solar_data"


@override_settings(ADMINS=[("Admin", "admin@example.com")])
class SolarDataTestBase(TestCase):
    """Shared setup for running solar_data against mocked Enphase API calls."""
    databases = "__all__"

    def setUp(self):
        AuthToken.objects.create(name="enphase", client_id="id", client_secret="secret",
                                 app_code="code", redirect_uri="https://example.com",
                                 access_token="access", refresh_token="refresh")

    def run_command(self, amounts, *extra_args):
        site_data = {"start_date": "2026-10-01"}
        with patch(f"{COMMAND}.env", return_value="enphase"), \
                patch(f"{COMMAND}.is_token_expired", return_value=False), \
                patch(f"{COMMAND}.get_site_production", return_value=site_data), \
                patch(f"{COMMAND}.get_production_amts", return_value=amounts):
            call_command("solar_data", "-s", "2026-10-01", "-e", "2026-10-03", *extra_args)


class SolarDataZeroAlertTestCase(SolarDataTestBase):
    def test_zero_production_emails_admins(self):
        self.run_command([1500, 0, 2000])

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
        self.assertIn("2026-10-02", mail.outbox[0].body)
        self.assertNotIn("2026-10-01", mail.outbox[0].body.split("\n\n")[0])
        self.assertEqual(SolarEnergy.objects.count(), 3)

    def test_no_zero_production_sends_no_email(self):
        self.run_command([1500, 1800, 2000])

        self.assertEqual(len(mail.outbox), 0)

    def test_existing_zero_day_sends_no_email(self):
        SolarEnergy.objects.create(date_of_production=date(2026, 10, 2), production=0)

        self.run_command([1500, 0, 2000])

        self.assertEqual(len(mail.outbox), 0)


class SolarDataUpdateTestCase(SolarDataTestBase):
    def setUp(self):
        super().setUp()
        SolarEnergy.objects.create(date_of_production=date(2026, 9, 30), production=999)

    def production_on(self, day):
        return SolarEnergy.objects.get(date_of_production=day).production

    def test_existing_days_unchanged_without_update(self):
        SolarEnergy.objects.create(date_of_production=date(2026, 10, 1), production=100)

        self.run_command([1500, 1800, 2000])

        self.assertEqual(self.production_on(date(2026, 10, 1)), 100)

    def test_update_overwrites_differing_days(self):
        SolarEnergy.objects.create(date_of_production=date(2026, 10, 1), production=100)
        SolarEnergy.objects.create(date_of_production=date(2026, 10, 2), production=1800)

        self.run_command([1500, 1800, 2000], "-u")

        self.assertEqual(self.production_on(date(2026, 10, 1)), 1500)
        self.assertEqual(self.production_on(date(2026, 10, 2)), 1800)
        self.assertEqual(self.production_on(date(2026, 10, 3)), 2000)
        self.assertEqual(self.production_on(date(2026, 9, 30)), 999)

    def test_update_in_test_mode_changes_nothing(self):
        SolarEnergy.objects.create(date_of_production=date(2026, 10, 1), production=100)

        self.run_command([1500, 1800, 2000], "-u", "-t")

        self.assertEqual(self.production_on(date(2026, 10, 1)), 100)
        self.assertFalse(SolarEnergy.objects.filter(date_of_production=date(2026, 10, 2)).exists())

    def test_update_to_zero_emails_admins(self):
        SolarEnergy.objects.create(date_of_production=date(2026, 10, 2), production=1800)

        self.run_command([1500, 0, 2000], "-u")

        self.assertEqual(self.production_on(date(2026, 10, 2)), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("2026-10-02", mail.outbox[0].body)
