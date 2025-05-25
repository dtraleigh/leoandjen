from django.test import TestCase

from data.functions import (get_car_miles_all_ytd_avg, get_car_miles_prev_ytd,
                            get_car_miles_ytd_total)
from data.models import CarMiles
from data.test_data.create_test_data import *
from data.year_vehicle_miles import VehicleMilesTraveledYear


class DataSimpleTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        create_test_data_water()
        create_test_data_elec_rates()
        create_test_data_elec()
        create_test_data_gas()
        create_test_data_vmt()

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
