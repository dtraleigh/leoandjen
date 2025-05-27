from datetime import datetime, date
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from data.models import Electricity
# from data.test_data.create_test_data import create_test_data_elec_rates, create_test_data_elec
from data.year_elec import ElecYear


class ElectricityTestCase(TestCase):
    databases = "__all__"
    fixtures = [
        # "data/test_data/test_data_Electricity.json",
        "data/test_data/test_data_ElectricRateSchedule.json",
    ]

    # @classmethod
    # def setUpTestData(cls):
    #     create_test_data_elec_rates()
    #     create_test_data_elec()

    def test_model_get_money_saved_by_solar1(self):
        # Case 1: More use, no credits. If we use more than we send
        bill1 = Electricity.objects.create(
            service_start_date=date(2023, 2, 1),
            service_end_date=date(2023, 2, 28),
            bill_date=date(2023, 3, 1),
            kWh_usage=333,
            solar_amt_sent_to_grid=222,
            net_metering_credit=Decimal("0.00"),
        )

        bill2 = Electricity.objects.create(
            service_start_date=date(2023, 3, 1),
            service_end_date=date(2023, 3, 31),
            bill_date=date(2023, 4, 1),
            kWh_usage=100,
            solar_amt_sent_to_grid=10,
            net_metering_credit=Decimal("0.00"),
        )

        # Refresh from DB to ensure any post-save logic has executed
        bill2.refresh_from_db()

        self.assertEqual(bill2.calculated_money_saved_by_solar, Decimal('1.21'))

    def test_model_get_money_saved_by_solar2(self):
        # Case 2: More use, small credits. If we use more than we send but we have some credits
        bill1 = Electricity.objects.create(
            service_start_date=date(2023, 2, 1),
            service_end_date=date(2023, 2, 28),
            bill_date=date(2023, 3, 1),
            kWh_usage=333,
            solar_amt_sent_to_grid=222,
            net_metering_credit=Decimal("20.00"),
        )

        bill2 = Electricity.objects.create(
            service_start_date=date(2023, 3, 1),
            service_end_date=date(2023, 3, 31),
            bill_date=date(2023, 4, 1),
            kWh_usage=100,
            solar_amt_sent_to_grid=10,
            net_metering_credit=Decimal("0.00"),
        )

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('3.63'))

    def test_model_get_money_saved_by_solar3(self):
        # Case 3: More use, big credits. If we use more than we send but we have lots of credits
        bill1 = Electricity.objects.create(
            service_start_date=date(2023, 2, 1),
            service_end_date=date(2023, 2, 28),
            bill_date=date(2023, 3, 1),
            kWh_usage=333,
            solar_amt_sent_to_grid=222,
            net_metering_credit=Decimal("120.00"),
        )

        bill2 = Electricity.objects.create(
            service_start_date=date(2023, 3, 1),
            service_end_date=date(2023, 3, 31),
            bill_date=date(2023, 4, 1),
            kWh_usage=100,
            solar_amt_sent_to_grid=10,
            net_metering_credit=Decimal("0.00"),
        )

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('12.09'))

    def test_model_get_money_saved_by_solar4(self):
        # Case 4: less use, no credits. If we use less than we send, no credits
        bill1 = Electricity.objects.create(
            service_start_date=date(2023, 2, 1),
            service_end_date=date(2023, 2, 28),
            bill_date=date(2023, 3, 1),
            kWh_usage=333,
            solar_amt_sent_to_grid=222,
            net_metering_credit=Decimal("0.00"),
        )

        bill2 = Electricity.objects.create(
            service_start_date=date(2023, 3, 1),
            service_end_date=date(2023, 3, 31),
            bill_date=date(2023, 4, 1),
            kWh_usage=50,
            solar_amt_sent_to_grid=100,
            net_metering_credit=Decimal("0.00"),
        )

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('6.05'))

    def test_model_get_money_saved_by_solar5(self):
        # Case 5: less use, existing credits. If we use less than we send and have credits
        bill1 = Electricity.objects.create(
            service_start_date=date(2023, 2, 1),
            service_end_date=date(2023, 2, 28),
            bill_date=date(2023, 3, 1),
            kWh_usage=333,
            solar_amt_sent_to_grid=222,
            net_metering_credit=Decimal("50.00"),
        )

        bill2 = Electricity.objects.create(
            service_start_date=date(2023, 3, 1),
            service_end_date=date(2023, 3, 31),
            bill_date=date(2023, 4, 1),
            kWh_usage=50,
            solar_amt_sent_to_grid=100,
            net_metering_credit=Decimal("0.00"),
        )

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('6.05'))

    def test_model_get_money_saved_by_solar6(self):
        # Case 6: Use exactly the same amount as credit
        bill1 = Electricity.objects.create(
            service_start_date=date(2023, 2, 1),
            service_end_date=date(2023, 2, 28),
            bill_date=date(2023, 3, 1),
            kWh_usage=333,
            solar_amt_sent_to_grid=222,
            net_metering_credit=Decimal("50.00"),
        )

        bill2 = Electricity.objects.create(
            service_start_date=date(2023, 3, 1),
            service_end_date=date(2023, 3, 31),
            bill_date=date(2023, 4, 1),
            kWh_usage=150,
            solar_amt_sent_to_grid=100,
            net_metering_credit=Decimal("0.00"),
        )

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('18.14'))

    def test_elec_usage_for_2022(self):
        call_command('loaddata', 'data/test_data/test_data_Electricity.json', verbosity=0)
        elec2022 = ElecYear(2022, "color")
        expected_for_2022 = [{'month_number': 1, 'month_str': 'Jan', 'days_in_month': 31, 'value': Decimal('937.78'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('937.78'), 'daily_consumption': Decimal('30.25')},
                             {'month_number': 2, 'month_str': 'Feb', 'days_in_month': 28, 'value': Decimal('700.72'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('700.72'), 'daily_consumption': Decimal('25.03')},
                             {'month_number': 3, 'month_str': 'Mar', 'days_in_month': 31, 'value': Decimal('567.08'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('567.08'), 'daily_consumption': Decimal('18.29')},
                             {'month_number': 4, 'month_str': 'Apr', 'days_in_month': 30, 'value': Decimal('479.66'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('479.66'), 'daily_consumption': Decimal('15.99')},
                             {'month_number': 5, 'month_str': 'May', 'days_in_month': 31, 'value': Decimal('590.83'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('590.83'), 'daily_consumption': Decimal('19.06')},
                             {'month_number': 6, 'month_str': 'Jun', 'days_in_month': 30, 'value': Decimal('726.52'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('726.52'), 'daily_consumption': Decimal('24.22')},
                             {'month_number': 7, 'month_str': 'Jul', 'days_in_month': 31, 'value': Decimal('855.78'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('855.78'), 'daily_consumption': Decimal('27.61')},
                             {'month_number': 8, 'month_str': 'Aug', 'days_in_month': 31, 'value': Decimal('818.38'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('818.38'), 'daily_consumption': Decimal('26.40')},
                             {'month_number': 9, 'month_str': 'Sept', 'days_in_month': 30, 'value': Decimal('595.50'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('595.50'), 'daily_consumption': Decimal('19.85')},
                             {'month_number': 10, 'month_str': 'Oct', 'days_in_month': 31, 'value': Decimal('502.52'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('502.52'), 'daily_consumption': Decimal('16.21')},
                             {'month_number': 11, 'month_str': 'Nov', 'days_in_month': 30, 'value': Decimal('576.62'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('576.62'), 'daily_consumption': Decimal('19.22')},
                             {'month_number': 12, 'month_str': 'Dec', 'days_in_month': 31, 'value': Decimal('850.10'),
                              'solar_produced': Decimal('0.00'), 'solar_sent_to_grid': Decimal('0.00'),
                              'grid_energy_consumed': Decimal('850.10'), 'daily_consumption': Decimal('27.42')}]
        self.assertEqual(elec2022.get_data_points(), expected_for_2022)

    def test_get_number_of_days(self):
        call_command('loaddata', 'data/test_data/test_data_Electricity.json', verbosity=0)
        elec = Electricity.objects.first()
        expected_days = (elec.service_end_date - elec.service_start_date).days + 1
        self.assertEqual(elec.get_number_of_days.days, expected_days)

    def test_get_previous_month_bill_returns_none_if_missing(self):
        jan_bill = Electricity.objects.create(
            bill_date=date(2024, 1, 20),
            service_start_date=date(2024, 1, 1),
            service_end_date=date(2024, 1, 31),
            kWh_usage=400,
            solar_amt_sent_to_grid=120,
            net_metering_credit=50,
        )
        self.assertIsNone(jan_bill.get_previous_month_bill)

    def test_get_previous_month_bill_returns_correct_previous(self):
        feb_bill = Electricity.objects.create(
            bill_date=date(2024, 2, 18),
            service_start_date=date(2024, 2, 1),
            service_end_date=date(2024, 2, 28),
            kWh_usage=380,
            solar_amt_sent_to_grid=100,
            net_metering_credit=40,
        )
        march_bill = Electricity.objects.create(
            bill_date=date(2024, 3, 18),
            service_start_date=date(2024, 3, 1),
            service_end_date=date(2024, 3, 31),
            kWh_usage=390,
            solar_amt_sent_to_grid=110,
            net_metering_credit=45,
        )
        self.assertEqual(march_bill.get_previous_month_bill, feb_bill)

    def test_get_previous_month_bill_across_year_boundary(self):
        dec_2024_bill = Electricity.objects.create(
            bill_date=date(2024, 12, 20),
            service_start_date=date(2024, 12, 1),
            service_end_date=date(2024, 12, 31),
            kWh_usage=420,
            solar_amt_sent_to_grid=130,
            net_metering_credit=55,
        )
        jan_2025_bill = Electricity.objects.create(
            bill_date=date(2025, 1, 22),
            service_start_date=date(2025, 1, 1),
            service_end_date=date(2025, 1, 31),
            kWh_usage=410,
            solar_amt_sent_to_grid=125,
            net_metering_credit=50,
        )
        self.assertEqual(jan_2025_bill.get_previous_month_bill, dec_2024_bill)

    def test_get_previous_month_bill_returns_none_if_month_skipped(self):
        feb_bill = Electricity.objects.create(
            bill_date=date(2024, 2, 18),
            service_start_date=date(2024, 2, 1),
            service_end_date=date(2024, 2, 29),
            kWh_usage=360,
            solar_amt_sent_to_grid=90,
            net_metering_credit=35,
        )
        april_bill = Electricity.objects.create(
            bill_date=date(2024, 4, 18),
            service_start_date=date(2024, 4, 1),
            service_end_date=date(2024, 4, 30),
            kWh_usage=370,
            solar_amt_sent_to_grid=95,
            net_metering_credit=38,
        )
        self.assertIsNone(april_bill.get_previous_month_bill)

    def test_get_money_saved_by_solar_returns_decimal(self):
        elec = Electricity.objects.create(
            bill_date=date(2024, 2, 11),
            service_start_date=date(2024, 2, 10),
            service_end_date=date(2024, 3, 9),
            kWh_usage=360,
            solar_amt_sent_to_grid=90,
            net_metering_credit=35,
        )
        saved = elec.get_money_saved_by_solar
        self.assertIsInstance(saved, Decimal)
        self.assertGreaterEqual(saved, Decimal("0.00"))

    def test_calculate_and_set_money_saved_sets_value(self):
        elec = Electricity.objects.create(
            bill_date=date(2024, 2, 11),
            service_start_date=date(2024, 2, 10),
            service_end_date=date(2024, 3, 9),
            kWh_usage=360,
            solar_amt_sent_to_grid=90,
            net_metering_credit=35,
        )
        elec.calculated_money_saved_by_solar = None
        elec.calculate_and_set_money_saved()
        self.assertIsNotNone(elec.calculated_money_saved_by_solar)
        self.assertIsInstance(elec.calculated_money_saved_by_solar, Decimal)
