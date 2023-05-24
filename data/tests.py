from datetime import datetime

from django.test import TestCase

from data.functions import (convert_years_string_to_years_list,
                            get_car_miles_all_ytd_avg, get_car_miles_prev_ytd,
                            get_car_miles_ytd_total)
from data.models import CarMiles
from data.test_data.create_test_data import *
from data.year_elec import ElecYear
from data.year_vehicle_miles import VehicleMilesTraveledYear


class DataSimpleTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        create_test_data_water()
        create_test_data_elec()
        create_test_data_gas()
        create_test_data_vmt()

    def test_clean_year_range_request(self):
        from data.functions import clean_year_range_request
        self.assertEqual(clean_year_range_request(None, "Electricity"), "2021-2023")
        self.assertEqual(clean_year_range_request("all", "Electricity"), "2021-2023")
        self.assertEqual(clean_year_range_request("ALL", "Electricity"), "2021-2023")
        self.assertEqual(clean_year_range_request("2022", "Electricity"), "2022")
        self.assertEqual(clean_year_range_request("2000", "Electricity"), "2000")
        self.assertEqual(clean_year_range_request("all", "CarMiles"), "2020-2023")
        self.assertEqual(clean_year_range_request("2020+", "CarMiles"), "2020-2023")
        self.assertEqual(clean_year_range_request("2020+", "Electricity"), "2020-2023")
        self.assertEqual(clean_year_range_request("2020+ ", "Electricity"), "2020-2023")

    def test_convert_years_string_to_years_list(self):
        self.assertEqual(convert_years_string_to_years_list("2020-2022"), [2020, 2021, 2022])
        self.assertEqual(convert_years_string_to_years_list("2020,2022"), [2020, 2022])
        self.assertEqual(convert_years_string_to_years_list("2020"), [2020])
        self.assertEqual(convert_years_string_to_years_list("202A"), [])

    def test_model_get_money_saved_by_solar1(self):
        # Case 1: More use, no credits. If we use more than we send
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.create(bill_date=datetime(2000, 2, 10),
                                           service_start_date=datetime(2000, 1, 11),
                                           service_end_date=datetime(2000, 2, 8),
                                           kWh_usage=333,
                                           solar_amt_sent_to_grid=222,
                                           net_metering_credit=0)
        bill2 = Electricity.objects.create(bill_date=datetime(2000, 3, 13),
                                           service_start_date=datetime(2000, 2, 9),
                                           service_end_date=datetime(2000, 3, 9),
                                           kWh_usage=100,
                                           solar_amt_sent_to_grid=10,
                                           net_metering_credit=0)

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('1.20'))
        bill1.delete()
        bill2.delete()

    def test_model_get_money_saved_by_solar2(self):
        # Case 2: More use, small credits. If we use more than we send but we have some credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.create(bill_date=datetime(2000, 2, 10),
                                           service_start_date=datetime(2000, 1, 11),
                                           service_end_date=datetime(2000, 2, 8),
                                           kWh_usage=333,
                                           solar_amt_sent_to_grid=222,
                                           net_metering_credit=20)
        bill2 = Electricity.objects.create(bill_date=datetime(2000, 3, 13),
                                           service_start_date=datetime(2000, 2, 9),
                                           service_end_date=datetime(2000, 3, 9),
                                           kWh_usage=100,
                                           solar_amt_sent_to_grid=10,
                                           net_metering_credit=0)

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('3.61'))
        bill1.delete()
        bill2.delete()

    def test_model_get_money_saved_by_solar3(self):
        # Case 3: More use, big credits. If we use more than we send but we have lots of credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.create(bill_date=datetime(2000, 2, 10),
                                           service_start_date=datetime(2000, 1, 11),
                                           service_end_date=datetime(2000, 2, 8),
                                           kWh_usage=333,
                                           solar_amt_sent_to_grid=222,
                                           net_metering_credit=120)
        bill2 = Electricity.objects.create(bill_date=datetime(2000, 3, 13),
                                           service_start_date=datetime(2000, 2, 9),
                                           service_end_date=datetime(2000, 3, 9),
                                           kWh_usage=100,
                                           solar_amt_sent_to_grid=10,
                                           net_metering_credit=0)

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('12.03'))
        bill1.delete()
        bill2.delete()

    def test_model_get_money_saved_by_solar4(self):
        # Case 4: less use, no credits. If we use less than we send, no credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.create(bill_date=datetime(2000, 2, 10),
                                           service_start_date=datetime(2000, 1, 11),
                                           service_end_date=datetime(2000, 2, 8),
                                           kWh_usage=333,
                                           solar_amt_sent_to_grid=222,
                                           net_metering_credit=0)
        bill2 = Electricity.objects.create(bill_date=datetime(2000, 3, 13),
                                           service_start_date=datetime(2000, 2, 9),
                                           service_end_date=datetime(2000, 3, 9),
                                           kWh_usage=50,
                                           solar_amt_sent_to_grid=100,
                                           net_metering_credit=0)

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('6.02'))
        bill1.delete()
        bill2.delete()

    def test_model_get_money_saved_by_solar5(self):
        # Case 5: less use, existing credits. If we use less than we send and have credits
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.create(bill_date=datetime(2000, 2, 10),
                                           service_start_date=datetime(2000, 1, 11),
                                           service_end_date=datetime(2000, 2, 8),
                                           kWh_usage=333,
                                           solar_amt_sent_to_grid=222,
                                           net_metering_credit=50)
        bill2 = Electricity.objects.create(bill_date=datetime(2000, 3, 13),
                                           service_start_date=datetime(2000, 2, 9),
                                           service_end_date=datetime(2000, 3, 9),
                                           kWh_usage=50,
                                           solar_amt_sent_to_grid=100,
                                           net_metering_credit=0)

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('6.02'))
        bill1.delete()
        bill2.delete()

    def test_model_get_money_saved_by_solar6(self):
        # Case 6: Use exactly the same amount as credit
        from decimal import Decimal

        from data.models import Electricity
        bill1 = Electricity.objects.create(bill_date=datetime(2000, 2, 10),
                                           service_start_date=datetime(2000, 1, 11),
                                           service_end_date=datetime(2000, 2, 8),
                                           kWh_usage=333,
                                           solar_amt_sent_to_grid=222,
                                           net_metering_credit=50)
        bill2 = Electricity.objects.create(bill_date=datetime(2000, 3, 13),
                                           service_start_date=datetime(2000, 2, 9),
                                           service_end_date=datetime(2000, 3, 9),
                                           kWh_usage=150,
                                           solar_amt_sent_to_grid=100,
                                           net_metering_credit=0)

        self.assertEqual(bill2.get_money_saved_by_solar, Decimal('18.05'))
        bill1.delete()
        bill2.delete()

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

    # def test_elec_get_ytd_totals(self):
    #     from data.functions import get_elec_dashboard_data
    #     data = get_elec_dashboard_data(datetime(2023, 2, 13))
    #     self.assertEqual(data["ytd_total"], 664.65)
    #     self.assertEqual(data["prev_ytd"], 937.78)
    #     self.assertEqual(data["all_ytd_avg"], 507)
    #     self.assertEqual(data["ytd_total"], 664.65)

    def test_elec_get_total_solar_produced_by_month(self):
        # Need to wait until I have more real data to play with
        pass

    def test_elec_get_months_solar_sent_to_grid(self):
        # Need to wait until I have more real data to play with
        pass

    def test_elec_get_months_grid_energy_consumed(self):
        # Need to wait until I have more real data to play with
        pass

    def test_car_miles_yearly_totals(self):
        vmt2020 = VehicleMilesTraveledYear(2020, "color")
        vmt2021 = VehicleMilesTraveledYear(2021, "color")
        vmt2022 = VehicleMilesTraveledYear(2022, "color")
        vmt2023 = VehicleMilesTraveledYear(2023, "color")

        self.assertEqual(vmt2020.get_total_miles, 13562)
        self.assertEqual(vmt2021.get_total_miles, 17035)
        self.assertEqual(vmt2022.get_total_miles, 10966)
        self.assertEqual(vmt2023.get_total_miles, 617)

    def test_car_miles_get_miles_per_month(self):
        vmt2020 = CarMiles.objects.filter(reading_date__year=2020)
        vmt2020_vmt_manual = [1552, 1332, 701, 113, 1545, 1900, 2352, 1151, 690, 563, 836, 827]

        for count, vmt in enumerate(vmt2020):
            self.assertEqual(vmt.get_miles_per_month, vmt2020_vmt_manual[count])

        vmt2021 = CarMiles.objects.filter(reading_date__year=2021)
        vmt2021_vmt_manual = [550, 1203, 1722, 1864, 1808, 1302, 2499, 1461, 741, 1508, 785, 1592]

        for count, vmt in enumerate(vmt2021):
            self.assertEqual(vmt.get_miles_per_month, vmt2021_vmt_manual[count])

    def test_car_miles_get_data_points(self):
        vmt2022 = VehicleMilesTraveledYear(2022, "color")
        vmt2022_data_points_manual = [{"month_number": 1, "month_str": "Jan", "value": 391},
                                      {"month_number": 2, "month_str": "Feb", "value": 896},
                                      {"month_number": 3, "month_str": "Mar", "value": 992},
                                      {"month_number": 4, "month_str": "Apr", "value": 999},
                                      {"month_number": 5, "month_str": "May", "value": 830},
                                      {"month_number": 6, "month_str": "Jun", "value": 545},
                                      {"month_number": 7, "month_str": "Jul", "value": 1513},
                                      {"month_number": 8, "month_str": "Aug", "value": 1254},
                                      {"month_number": 9, "month_str": "Sept", "value": 973},
                                      {"month_number": 10, "month_str": "Oct", "value": 718},
                                      {"month_number": 11, "month_str": "Nov", "value": 1565},
                                      {"month_number": 12, "month_str": "Dec", "value": 290}]

        vmt2023 = VehicleMilesTraveledYear(2023, "color")
        vmt2023_data_points_manual = [{"month_number": 1, "month_str": "Jan", "value": 617}]

        self.assertEqual(vmt2022.get_data_points(), vmt2022_data_points_manual)
        self.assertEqual(vmt2023.get_data_points(), vmt2023_data_points_manual)

    def test_car_miles_get_ytd_miles(self):
        vmt2022 = VehicleMilesTraveledYear(2022, "color")

        self.assertEqual(vmt2022.get_ytd_miles(), 391)
        self.assertEqual(vmt2022.get_ytd_miles(CarMiles.objects.get(reading_date__year=2023,
                                                                    reading_date__month=1)), 0)
        self.assertEqual(vmt2022.get_ytd_miles(CarMiles.objects.get(reading_date__year=2022,
                                                                    reading_date__month=12)), 10676)
        self.assertEqual(vmt2022.get_ytd_miles(CarMiles.objects.get(reading_date__year=2022,
                                                                    reading_date__month=11)), 9111)

        vmt2020 = VehicleMilesTraveledYear(2020, "color")

        self.assertEqual(vmt2020.get_ytd_miles(), 1552)
        self.assertEqual(vmt2020.get_ytd_miles(CarMiles.objects.get(reading_date__year=2023,
                                                                    reading_date__month=1)), 0)
        self.assertEqual(vmt2020.get_ytd_miles(CarMiles.objects.get(reading_date__year=2022,
                                                                    reading_date__month=12)), 12735)
        self.assertEqual(vmt2020.get_ytd_miles(CarMiles.objects.get(reading_date__year=2022,
                                                                    reading_date__month=11)), 11899)

    def test_car_miles_get_car_miles_ytd_total(self):
        self.assertEqual(get_car_miles_ytd_total(), 617)
        self.assertEqual(get_car_miles_ytd_total(CarMiles.objects.get(reading_date__month=1, reading_date__year=2022)),
                         0)
        self.assertEqual(get_car_miles_ytd_total(CarMiles.objects.get(reading_date__month=2, reading_date__year=2022)),
                         391)
        self.assertEqual(get_car_miles_ytd_total(CarMiles.objects.get(reading_date__month=12, reading_date__year=2021)),
                         15443)

    def test_car_miles_get_car_miles_prev_ytd(self):
        self.assertEqual(get_car_miles_prev_ytd(), 391)
        self.assertEqual(get_car_miles_prev_ytd(CarMiles.objects.get(reading_date__month=1, reading_date__year=2022)),
                         0)
        self.assertEqual(get_car_miles_prev_ytd(CarMiles.objects.get(reading_date__month=2, reading_date__year=2022)),
                         550)
        self.assertEqual(get_car_miles_prev_ytd(CarMiles.objects.get(reading_date__month=12, reading_date__year=2021)),
                         12735)

    def test_car_miles_get_car_miles_all_ytd_avg(self):
        self.assertEqual(get_car_miles_all_ytd_avg(), 831)
        self.assertEqual(
            get_car_miles_all_ytd_avg(CarMiles.objects.get(reading_date__month=1, reading_date__year=2022)), 0)
        self.assertEqual(
            get_car_miles_all_ytd_avg(CarMiles.objects.get(reading_date__month=2, reading_date__year=2022)), 1051)
        self.assertEqual(
            get_car_miles_all_ytd_avg(CarMiles.objects.get(reading_date__month=12, reading_date__year=2021)), 12735)
