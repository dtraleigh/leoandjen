import logging
import tempfile
from urllib.parse import urlparse

import pdfplumber
import re
from datetime import datetime

import requests

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

# Suppress pdfminer warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def parse_month_day(month_str, day_str, year):
    return datetime(year, MONTHS[month_str], int(day_str)).date()

def extract_elec_billing_date(text):
    match = re.search(r'Bill date\s+([A-Za-z]{3}) (\d{1,2}), (\d{4})', text)
    if match:
        month, day, year = match.groups()
        return parse_month_day(month, day, int(year))
    return None

def extract_elec_service_dates(text, billing_year):
    match = re.search(r'For service\s+([A-Za-z]{3}) (\d{1,2})\s*-\s*([A-Za-z]{3}) (\d{1,2})', text)
    if match:
        start_month, start_day, end_month, end_day = match.groups()

        start_month_num = MONTHS[start_month]
        end_month_num = MONTHS[end_month]

        # If the start month number is greater, it must be in the previous year
        if start_month_num > end_month_num:
            start_year = billing_year - 1
            end_year = billing_year
        else:
            start_year = end_year = billing_year

        start_date = parse_month_day(start_month, start_day, start_year)
        end_date = parse_month_day(end_month, end_day, end_year)
        return start_date, end_date

    return None, None

def extract_elec_energy_used(text):
    usage_section = re.search(r'Current electric usage for meter number.*?(?=Energy Delivered)', text, re.DOTALL)
    if usage_section:
        match = re.search(r'Energy Used\s+(\d+(?:\.\d+)?)\s*kWh', usage_section.group())
        if match:
            return float(match.group(1))
    return None

def extract_elec_actual_reading(text):
    usage_section = re.search(r'Current electric usage for meter number.*?(?=Energy Delivered)', text, re.DOTALL)
    if usage_section:
        match = re.search(r'Actual reading on\s+[A-Za-z]{3}\s+\d{1,2}\s+(\d+)', usage_section.group())
        if match:
            return int(match.group(1))
    return None

def extract_elec_previous_reading(text):
    usage_section = re.search(r'Current electric usage for meter number.*?(?=Energy Delivered)', text, re.DOTALL)
    if usage_section:
        match = re.search(r'Previous reading on\s+[A-Za-z]{3}\s+\d{1,2}\s*-\s*(\d+)', usage_section.group())
        if match:
            return int(match.group(1))
    return None

def extract_energy_delivered_to_grid(text):
    delivered_section = re.search(r'Energy Delivered.*?(?=Billed kWh)', text, re.DOTALL)
    if delivered_section:
        match = re.search(r'Energy delivered to grid\s+(\d+(?:\.\d+)?)\s*kWh', delivered_section.group())
        if match:
            return float(match.group(1))
    return None

def extract_delivered_actual_reading(text):
    delivered_section = re.search(r'Energy Delivered.*?(?=Billed kWh)', text, re.DOTALL)
    if delivered_section:
        match = re.search(r'Actual reading on\s+[A-Za-z]{3}\s+\d{1,2}\s+(\d+)', delivered_section.group())
        if match:
            return int(match.group(1))
    return None

def extract_delivered_previous_reading(text):
    delivered_section = re.search(r'Energy Delivered.*?(?=Billed kWh)', text, re.DOTALL)
    if delivered_section:
        match = re.search(r'Previous reading on\s+[A-Za-z]{3}\s+\d{1,2}\s*-\s*(\d+)', delivered_section.group())
        if match:
            return int(match.group(1))
    return None

def extract_carried_forward_balance(text):
    """
    Extracts the 'Carried Forward Balance' value from the Net Metering Summary section.
    If not found, returns 0.
    """
    # Look for the exact line 'Carried Forward Balance' followed by a number and 'kWh'
    match = re.search(r'Carried Forward Balance\s+(-?\d+)\s*kWh', text)
    if match:
        return int(match.group(1))
    return 0


def extract_gas_billing_date(text):
    # Look for the statement date in the table format
    # STATEMENT DATE DATE DUE AMOUNT DUE
    # May 8 2025 Jun 6 2025 $22.33
    match = re.search(r'STATEMENT DATE.*?([A-Za-z]{3}) (\d{1,2}) (\d{4})', text, re.DOTALL)
    if match:
        month, day, year = match.groups()
        return parse_month_day(month, day, int(year))
    return None


def extract_gas_service_dates(text, year):
    # Look for the billing period in the meter table
    # Format: 04/07/25-05/07/25
    match = re.search(r'BILLING PERIOD.*?(\d{2})/(\d{2})/(\d{2})-(\d{2})/(\d{2})/(\d{2})', text, re.DOTALL)
    if match:
        start_month, start_day, start_year, end_month, end_day, end_year = match.groups()

        # Convert 2-digit years to 4-digit (assuming 20xx)
        start_year_full = 2000 + int(start_year)
        end_year_full = 2000 + int(end_year)

        # Convert month numbers to month names for parse_month_day
        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                       7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

        start_month_name = month_names[int(start_month)]
        end_month_name = month_names[int(end_month)]

        start_date = parse_month_day(start_month_name, start_day, start_year_full)
        end_date = parse_month_day(end_month_name, end_day, end_year_full)

        return start_date, end_date
    return None, None


def extract_gas_therms_usage(text):
    # Look for the therms value in the meter table
    # The pattern shows: THERMS column with value like "= 10"
    match = re.search(r'THERMS.*?=\s*(\d+(?:\.\d+)?)', text, re.DOTALL)
    if match:
        return float(match.group(1))

    # Alternative pattern in case the format is different
    match = re.search(r'THERMS\s+(\d+(?:\.\d+)?)', text)
    if match:
        return float(match.group(1))

    return None


def get_text_from_pdf(source):
    """
    Extract text from a PDF, either from a local file or from a remote URL.
    """
    parsed = urlparse(source)
    is_remote = parsed.scheme in ("http", "https")

    if is_remote:
        response = requests.get(source)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(response.content)
            tmp.flush()

            with pdfplumber.open(tmp.name) as pdf:
                return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    else:
        # Assume it's a local file path
        with pdfplumber.open(source) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())


def get_bill_type(text):
    text_lower = text.lower()
    if "duke-energy" in text_lower or "duke energy" in text_lower:
        return "Electricity"
    elif "enbridge gas north carolina" in text_lower:
        return "Gas"
    return None


def extract_pdf_data_for_preview(pdf_path):
    text = get_text_from_pdf(pdf_path)
    bill_type = get_bill_type(text)

    if bill_type == "Electricity":
        return get_elec_preview_data(text)
    elif bill_type == "Gas":
        return get_gas_preview_data(text)
    return None


def get_elec_preview_data(text):
    billing_date = extract_elec_billing_date(text)
    start_date, end_date = extract_elec_service_dates(text, billing_date.year)
    energy_used = extract_elec_energy_used(text)
    actual_reading = extract_elec_actual_reading(text)
    previous_reading = extract_elec_previous_reading(text)
    carried_forward_balance = extract_carried_forward_balance(text)
    energy_delivered_to_grid = extract_energy_delivered_to_grid(text)
    delivered_actual_reading = extract_delivered_actual_reading(text)
    delivered_previous_reading = extract_delivered_previous_reading(text)

    # Optional: Validate energy usage matches meter difference
    if actual_reading and previous_reading and energy_used is not None:
        diff = actual_reading - previous_reading
        if abs(diff - energy_used) > 0.1:
            raise ValueError(f"Usage mismatch: Meter says {diff}, but reported is {energy_used}")

    return {
        "bill_type": "Electricity",
        "billing_date": billing_date.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "electricity_usage_kwh": energy_used,
        "actual_reading": actual_reading,
        "previous_reading": previous_reading,
        "carried_forward_balance": carried_forward_balance,
        "energy_delivered_to_grid": energy_delivered_to_grid,
        "delivered_actual_reading": delivered_actual_reading,
        "delivered_previous_reading": delivered_previous_reading
    }


def extract_elec_pdf_data_for_saving(pdf_path):
    text = get_text_from_pdf(pdf_path)

    billing_date = extract_elec_billing_date(text)
    start_date, end_date = extract_elec_service_dates(text, billing_date.year)
    energy_used = extract_elec_energy_used(text)
    actual_reading = extract_elec_actual_reading(text)
    previous_reading = extract_elec_previous_reading(text)
    carried_forward_balance = extract_carried_forward_balance(text)
    energy_delivered_to_grid = extract_energy_delivered_to_grid(text)
    delivered_actual_reading = extract_delivered_actual_reading(text)
    delivered_previous_reading = extract_delivered_previous_reading(text)

    # Optional: Validate energy usage matches meter difference
    if actual_reading and previous_reading and energy_used is not None:
        diff = actual_reading - previous_reading
        if abs(diff - energy_used) > 0.1:
            raise ValueError(f"Usage mismatch: Meter says {diff}, but reported is {energy_used}")

    return {
        "bill_type": "Electricity",
        "billing_date": billing_date,
        "start_date": start_date,
        "end_date": end_date,
        "electricity_usage_kwh": energy_used,
        "actual_reading": actual_reading,
        "previous_reading": previous_reading,
        "carried_forward_balance": carried_forward_balance,
        "energy_delivered_to_grid": energy_delivered_to_grid,
        "delivered_actual_reading": delivered_actual_reading,
        "delivered_previous_reading": delivered_previous_reading
    }


def get_gas_preview_data(text):
    billing_date = extract_gas_billing_date(text)
    start_date, end_date = extract_gas_service_dates(text, billing_date.year)
    therms_usage = extract_gas_therms_usage(text)

    return {
        "bill_type": "Gas",
        "billing_date": billing_date.isoformat(),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "therms_usage": therms_usage
    }


def extract_gas_pdf_data_for_saving(pdf_path):
    text = get_text_from_pdf(pdf_path)

    billing_date = extract_gas_billing_date(text)
    start_date, end_date = extract_gas_service_dates(text, billing_date.year)
    therms_usage = extract_gas_therms_usage(text)

    return {
        "bill_type": "Gas",
        "billing_date": billing_date,
        "start_date": start_date,
        "end_date": end_date,
        "therms_usage": therms_usage
    }