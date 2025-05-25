from datetime import datetime, date
from decimal import Decimal

from django.test import TestCase

from data.models import Electricity
from data.test_data.create_test_data import create_test_data_elec_rates, create_test_data_elec
from data.year_elec import ElecYear


class ElectricityTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        create_test_data_elec_rates()
        create_test_data_elec()

    def test_model_get_money_saved_by_solar1(self):
        # Case 1: More use, no credits. If we use more than we send
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.get(bill_date=datetime(2023, 2, 10))
        bill1.kWh_usage = 333
        bill1.solar_amt_sent_to_grid = 222
        bill1.net_metering_credit = 0
        bill1.save()

        bill2 = Electricity.objects.get(bill_date=datetime(2023, 3, 13))
        bill2.kWh_usage = 100
        bill2.solar_amt_sent_to_grid = 10
        bill2.net_metering_credit = 0
        bill2.save()

        self.assertEqual(bill2.calculated_money_saved_by_solar, Decimal('1.21'))

    def test_model_get_money_saved_by_solar2(self):
        # Case 2: More use, small credits. If we use more than we send but we have some credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.get(bill_date=datetime(2023, 2, 10))
        bill1.kWh_usage = 333
        bill1.solar_amt_sent_to_grid = 222
        bill1.net_metering_credit = 20
        bill1.save()

        bill2 = Electricity.objects.get(bill_date=datetime(2023, 3, 13))
        bill2.kWh_usage = 100
        bill2.solar_amt_sent_to_grid = 10
        bill2.net_metering_credit = 0
        bill2.save()

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('3.63'))

    def test_model_get_money_saved_by_solar3(self):
        # Case 3: More use, big credits. If we use more than we send but we have lots of credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.get(bill_date=datetime(2023, 2, 10))
        bill1.kWh_usage = 333
        bill1.solar_amt_sent_to_grid = 222
        bill1.net_metering_credit = 120
        bill1.save()

        bill2 = Electricity.objects.get(bill_date=datetime(2023, 3, 13))
        bill2.kWh_usage = 100
        bill2.solar_amt_sent_to_grid = 10
        bill2.net_metering_credit = 0
        bill2.save()

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('12.09'))

    def test_model_get_money_saved_by_solar4(self):
        # Case 4: less use, no credits. If we use less than we send, no credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.get(bill_date=datetime(2023, 2, 10))
        bill1.kWh_usage = 333
        bill1.solar_amt_sent_to_grid = 222
        bill1.net_metering_credit = 0
        bill1.save()

        bill2 = Electricity.objects.get(bill_date=datetime(2023, 3, 13))
        bill2.kWh_usage = 50
        bill2.solar_amt_sent_to_grid = 100
        bill2.net_metering_credit = 0
        bill2.save()

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('6.05'))

    def test_model_get_money_saved_by_solar5(self):
        # Case 5: less use, existing credits. If we use less than we send and have credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.get(bill_date=datetime(2023, 2, 10))
        bill1.kWh_usage = 333
        bill1.solar_amt_sent_to_grid = 222
        bill1.net_metering_credit = 50
        bill1.save()

        bill2 = Electricity.objects.get(bill_date=datetime(2023, 3, 13))
        bill2.kWh_usage = 50
        bill2.solar_amt_sent_to_grid = 100
        bill2.net_metering_credit = 0
        bill2.save()

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('6.05'))

    def test_model_get_money_saved_by_solar6(self):
        # Case 6: Use exactly the same amount as credit
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.get(bill_date=datetime(2023, 2, 10))
        bill1.kWh_usage = 333
        bill1.solar_amt_sent_to_grid = 222
        bill1.net_metering_credit = 50
        bill1.save()

        bill2 = Electricity.objects.get(bill_date=datetime(2023, 3, 13))
        bill2.kWh_usage = 150
        bill2.solar_amt_sent_to_grid = 100
        bill2.net_metering_credit = 0
        bill2.save()

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('18.14'))

    def test_elec_usage_for_2022(self):
        from decimal import Decimal

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
        elec = Electricity.objects.first()
        expected_days = (elec.service_end_date - elec.service_start_date).days + 1
        self.assertEqual(elec.get_number_of_days.days, expected_days)

    def test_get_bill_before_this_one_returns_none_if_first(self):
        earliest = Electricity.objects.order_by("service_start_date").first()
        self.assertIsNone(earliest.get_bill_before_this_one)

    def test_get_bill_before_this_one_across_year_boundary(self):
        january_bill = Electricity.objects.get(id=96)
        december_bill = Electricity.objects.get(id=95)
        
        prev_bill = january_bill.get_bill_before_this_one
        self.assertEqual(prev_bill, december_bill)

    def test_get_bill_before_this_one_returns_previous(self):
        bills = list(Electricity.objects.order_by("service_start_date"))
        if len(bills) >= 2:
            second = bills[1]
            first = bills[0]
            self.assertEqual(second.get_bill_before_this_one, first)

    # def test_get_money_saved_by_solar_returns_decimal(self):
    #     elec = Electricity.objects.order_by("service_start_date").last()
    #     saved = elec.get_money_saved_by_solar
    #     self.assertIsInstance(saved, Decimal)
    #     self.assertGreaterEqual(saved, Decimal("0.00"))
    #
    # def test_calculate_and_set_money_saved_sets_value(self):
    #     elec = Electricity.objects.order_by("service_start_date").last()
    #     elec.calculated_money_saved_by_solar = None
    #     elec.calculate_and_set_money_saved()
    #     self.assertIsNotNone(elec.calculated_money_saved_by_solar)
    #     self.assertIsInstance(elec.calculated_money_saved_by_solar, Decimal)
