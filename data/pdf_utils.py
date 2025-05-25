import pdfplumber
import re
from datetime import datetime

MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def parse_month_day(month_str, day_str, year):
    return datetime(year, MONTHS[month_str], int(day_str)).date()

def extract_billing_date(text):
    match = re.search(r'Bill date\s+([A-Za-z]{3}) (\d{1,2}), (\d{4})', text)
    if match:
        month, day, year = match.groups()
        return parse_month_day(month, day, int(year))
    return None

def extract_service_dates(text, billing_year):
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

def extract_energy_used(text):
    usage_section = re.search(r'Current electric usage for meter number.*?(?=Energy Delivered)', text, re.DOTALL)
    if usage_section:
        match = re.search(r'Energy Used\s+(\d+(?:\.\d+)?)\s*kWh', usage_section.group())
        if match:
            return float(match.group(1))
    return None

def extract_actual_reading(text):
    usage_section = re.search(r'Current electric usage for meter number.*?(?=Energy Delivered)', text, re.DOTALL)
    if usage_section:
        match = re.search(r'Actual reading on\s+[A-Za-z]{3}\s+\d{1,2}\s+(\d+)', usage_section.group())
        if match:
            return int(match.group(1))
    return None

def extract_previous_reading(text):
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


def get_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"  # add spacing between pages

    return text


def extract_pdf_data_for_preview(pdf_path):
    text = get_text_from_pdf(pdf_path)

    billing_date = extract_billing_date(text)
    start_date, end_date = extract_service_dates(text, billing_date.year)
    energy_used = extract_energy_used(text)
    actual_reading = extract_actual_reading(text)
    previous_reading = extract_previous_reading(text)
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

def extract_pdf_data_for_saving(pdf_path):
    text = get_text_from_pdf(pdf_path)

    billing_date = extract_billing_date(text)
    start_date, end_date = extract_service_dates(text, billing_date.year)
    energy_used = extract_energy_used(text)
    actual_reading = extract_actual_reading(text)
    previous_reading = extract_previous_reading(text)
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