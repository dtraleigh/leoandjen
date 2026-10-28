from datetime import date

from django.core.management import call_command
from django.test import TestCase

from data.models import SolarEnergy


class FillSolarGapTestCase(TestCase):
    databases = "__all__"

    def setUp(self):
        # Last year's source data
        for day, amt in [(1, 1000), (2, 2000), (3, 3000), (4, 4000)]:
            SolarEnergy.objects.create(date_of_production=date(2025, 9, day), production=amt)
        SolarEnergy.objects.create(date_of_production=date(2025, 9, 5), production=0)

        # This year's gap: zeros, one missing day (9/2), one real day (9/4), one with a 0 source (9/5)
        SolarEnergy.objects.create(date_of_production=date(2026, 9, 1), production=0)
        SolarEnergy.objects.create(date_of_production=date(2026, 9, 3), production=0)
        SolarEnergy.objects.create(date_of_production=date(2026, 9, 4), production=4500)
        SolarEnergy.objects.create(date_of_production=date(2026, 9, 5), production=0)
        SolarEnergy.objects.create(date_of_production=date(2026, 9, 6), production=0)

    def production_on(self, day):
        return SolarEnergy.objects.get(date_of_production=day).production

    def test_fills_gap_from_previous_year(self):
        call_command("fill_solar_gap", "-s", "2026-09-01", "-e", "2026-09-06")

        self.assertEqual(self.production_on(date(2026, 9, 1)), 1000)
        self.assertEqual(self.production_on(date(2026, 9, 2)), 2000)
        self.assertEqual(self.production_on(date(2026, 9, 3)), 3000)
        # Real data is left alone
        self.assertEqual(self.production_on(date(2026, 9, 4)), 4500)
        # 0 source and missing source are left at 0
        self.assertEqual(self.production_on(date(2026, 9, 5)), 0)
        self.assertEqual(self.production_on(date(2026, 9, 6)), 0)

    def test_test_mode_changes_nothing(self):
        call_command("fill_solar_gap", "-s", "2026-09-01", "-e", "2026-09-06", "-t")

        self.assertEqual(self.production_on(date(2026, 9, 1)), 0)
        self.assertFalse(SolarEnergy.objects.filter(date_of_production=date(2026, 9, 2)).exists())

    def test_leap_day_uses_feb_28(self):
        SolarEnergy.objects.create(date_of_production=date(2027, 2, 28), production=1234)

        call_command("fill_solar_gap", "-s", "2028-02-29", "-e", "2028-02-29")

        self.assertEqual(self.production_on(date(2028, 2, 29)), 1234)
