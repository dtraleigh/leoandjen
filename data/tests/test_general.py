from datetime import datetime

from django.test import TestCase

from data.functions import convert_years_string_to_years_list
from data.test_data.create_test_data import *


class DataTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        create_test_data_water()
        create_test_data_elec_rates()
        create_test_data_elec()
        create_test_data_gas()
        create_test_data_vmt()

    def test_clean_year_range_request(self):
        from data.functions import clean_year_range_request
        current_year = datetime.now().year
        self.assertEqual(clean_year_range_request(None, "Electricity"), f"{current_year - 2}-{current_year}")
        self.assertEqual(clean_year_range_request("all", "Electricity"), "2015-2023")
        self.assertEqual(clean_year_range_request("ALL", "Electricity"), "2015-2023")
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
