import logging
from datetime import datetime
from data.pdf_utils import (
    extract_elec_billing_date,
    extract_elec_service_dates, extract_elec_energy_used, extract_elec_actual_reading, extract_elec_previous_reading,
    extract_energy_delivered_to_grid, extract_delivered_actual_reading, extract_delivered_previous_reading,
    extract_carried_forward_balance, get_text_from_pdf, get_bill_type, extract_gas_billing_date,
    extract_gas_service_dates, extract_gas_therms_usage
)

from django.test import TestCase

from data.functions import convert_years_string_to_years_list
from data.test_data.create_test_data import *

# Suppress pdfminer warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)

class DataTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        create_test_data_water()
        create_test_data_elec_rates()
        create_test_data_elec()
        create_test_data_gas()
        create_test_data_vmt()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.expected_elec_data = {
            "data/test_data/elec_bill_nov24.pdf": {
                "billing_date": "2024-12-10",
                "billing_year": 2024,
                "service_start": "2024-11-09",
                "service_end": "2024-12-07",
                "energy_used": 477,
                "actual_reading": 38538,
                "previous_reading": 38061,
                "energy_delivered": 360,
                "delivered_actual_reading": 10345,
                "delivered_previous_reading": 9985,
                "carried_forward_balance": 122
            },
            "data/test_data/elec_bill_dec24.pdf": {
                "billing_date": "2025-01-14",
                "billing_year": 2025,
                "service_start": "2024-12-08",
                "service_end": "2025-01-10",
                "energy_used": 739,
                "actual_reading": 39277,
                "previous_reading": 38538,
                "energy_delivered": 341,
                "delivered_actual_reading": 10686,
                "delivered_previous_reading": 10345,
                "carried_forward_balance": 0
            },
            "data/test_data/elec_bill_jan25.pdf": {
                "billing_date": "2025-02-13",
                "billing_year": 2025,
                "service_start": "2025-01-11",
                "service_end": "2025-02-11",
                "energy_used": 675,
                "actual_reading": 39952,
                "previous_reading": 39277,
                "energy_delivered": 392,
                "delivered_actual_reading": 11078,
                "delivered_previous_reading": 10686,
                "carried_forward_balance": 0
            },
            "data/test_data/elec_bill_feb25.pdf": {
                "billing_date": "2025-03-13",
                "billing_year": 2025,
                "service_start": "2025-02-12",
                "service_end": "2025-03-11",
                "energy_used": 510,
                "actual_reading": 40462,
                "previous_reading": 39952,
                "energy_delivered": 435,
                "delivered_actual_reading": 11513,
                "delivered_previous_reading": 11078,
                "carried_forward_balance": 0
            },
            "data/test_data/elec_bill_mar25.pdf": {
                "billing_date": "2025-04-11",
                "billing_year": 2025,
                "service_start": "2025-03-12",
                "service_end": "2025-04-09",
                "energy_used": 224,
                "actual_reading": 40686,
                "previous_reading": 40462,
                "energy_delivered": 584,
                "delivered_actual_reading": 12097,
                "delivered_previous_reading": 11513,
                "carried_forward_balance": 360
            },
            "data/test_data/elec_bill_apr25.pdf": {
                "billing_date": "2025-05-13",
                "billing_year": 2025,
                "service_start": "2025-04-10",
                "service_end": "2025-05-09",
                "energy_used": 299,
                "actual_reading": 40985,
                "previous_reading": 40686,
                "energy_delivered": 593,
                "delivered_actual_reading": 12690,
                "delivered_previous_reading": 12097,
                "carried_forward_balance": 0
            },
        }
        cls.expected_gas_data = {
            "data/test_data/gas_bill_apr25.pdf": {
                "billing_date": "2025-05-08",
                "billing_year": 2025,
                "service_start": "2025-04-07",
                "service_end": "2025-05-07",
                "therms_usage": 10,
            }
        }

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

    def test_extract_billing_date(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            result = extract_elec_billing_date(text)
            self.assertEqual(result.isoformat(), data["billing_date"], f"Failed billing_date on {filename}")

        for filename, data in self.expected_gas_data.items():
            text = get_text_from_pdf(filename)
            result = extract_gas_billing_date(text)
            self.assertEqual(result.isoformat(), data["billing_date"], f"Failed billing_date on {filename}")

    def test_extract_service_dates(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            start, end = extract_elec_service_dates(text, data["billing_year"])
            self.assertEqual(start.isoformat(), data["service_start"], f"Failed service_start on {filename}")
            self.assertEqual(end.isoformat(), data["service_end"], f"Failed service_end on {filename}")

        for filename, data in self.expected_gas_data.items():
            text = get_text_from_pdf(filename)
            start, end = extract_gas_service_dates(text, data["billing_year"])
            self.assertEqual(start.isoformat(), data["service_start"], f"Failed service_start on {filename}")
            self.assertEqual(end.isoformat(), data["service_end"], f"Failed service_end on {filename}")

    def test_extract_energy_used(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            result = extract_elec_energy_used(text)
            self.assertEqual(result, data["energy_used"], msg=f"{filename} failed")

    def test_extract_actual_reading(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            result = extract_elec_actual_reading(text)
            self.assertEqual(result, data["actual_reading"], msg=f"{filename} failed")

    def test_extract_previous_reading(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            result = extract_elec_previous_reading(text)
            self.assertEqual(result, data["previous_reading"], msg=f"{filename} failed")

    def test_extract_energy_delivered_to_grid(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf( filename)
            result = extract_energy_delivered_to_grid(text)
            self.assertEqual(result, data["energy_delivered"], msg=f"{filename} failed")

    def test_extract_delivered_actual_reading(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            result = extract_delivered_actual_reading(text)
            self.assertEqual(result, data["delivered_actual_reading"], msg=f"{filename} failed")

    def test_extract_delivered_previous_reading(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            result = extract_delivered_previous_reading(text)
            self.assertEqual(result, data["delivered_previous_reading"], msg=f"{filename} failed")

    def test_extract_carried_forward_balance(self):
        for filename, data in self.expected_elec_data.items():
            text = get_text_from_pdf(filename)
            result = extract_carried_forward_balance(text)
            self.assertEqual(result, data["carried_forward_balance"], msg=f"{filename} failed")

    def test_extract_gas_therms_usage(self):
        for filename, data in self.expected_gas_data.items():
            text = get_text_from_pdf(filename)
            result = extract_gas_therms_usage(text)
            self.assertEqual(result, data["therms_usage"], msg=f"{filename} failed")

    def test_get_bill_type(self):
        # Test cases that should return "Electricity"
        electricity_text_strings = [
            "This is a bill from duke-energy for electricity service.",
            "This is a bill from DUKE-ENERGY for electricity service.",
            "This is a bill from Duke-Energy for electricity service.",
            "This is a bill from duke energy for electricity service.",
            "This is a bill from DUKE ENERGY for electricity service.",
            "This is a bill from Duke Energy for electricity service.",
            "Duke Energy bill for duke-energy customer service from Duke Energy.",
            "duke-energy is your electricity provider.",
            "Your electricity bill is from duke energy",
            "Bill from: DUKE-ENERGY! Thank you for your business.",
            """
            Electric Utility Bill
            Provider: Duke Energy
            Account Number: 123456789
            """
        ]

        for text in electricity_text_strings:
            result = get_bill_type(text)
            self.assertEqual(result, "Electricity", f"Failed for text: {text[:50]}...")

        # Test cases that should return "Gas"
        gas_text_strings = [
            "This is a bill from enbridge gas north carolina for natural gas service.",
            "This is a bill from ENBRIDGE GAS NORTH CAROLINA for natural gas service.",
            "This is a bill from Enbridge Gas North Carolina for natural gas service.",
            "enbridge gas north carolina is your gas provider.",
            "Your gas bill is from enbridge gas north carolina",
            "Bill statement from: ENBRIDGE GAS NORTH CAROLINA. Thank you.",
            """
            Natural Gas Utility Bill
            Provider: Enbridge Gas North Carolina
            Account Number: 987654321
            """
        ]

        for text in gas_text_strings:
            result = get_bill_type(text)
            self.assertEqual(result, "Gas", f"Failed for text: {text[:50]}...")

        # Test cases that should return None
        none_text_strings = [
            "This is a bill from another utility company.",
            "This is a bill from duke power company.",
            "This is an energy bill from another company.",
            "This is a bill from duke-power or energy-duke company.",
            "This is a bill from enbridge gas virginia.",  # Different state
            "This is a bill from enbridge north carolina.",  # Missing "gas"
            "",
            "   \n\t  "
        ]

        for text in none_text_strings:
            result = get_bill_type(text)
            self.assertIsNone(result, f"Failed for text: {text[:50]}...")

        # Test None input raises error
        with self.assertRaises(AttributeError):
            get_bill_type(None)
