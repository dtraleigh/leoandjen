import csv
import logging
import os
from datetime import datetime, date
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from data.functions import *
from data.models import *
from data.pdf_utils import extract_pdf_data_for_preview, extract_pdf_data_for_saving
from data.year_elec import ElecYear
from data.year_gas import GasYear
from data.year_vehicle_miles import VehicleMilesTraveledYear
from data.year_water import WaterYear

logger = logging.getLogger("django")

colors = ["rgba(0, 86, 71, 0.8)",
          "rgba(56, 85, 178, 0.8)",
          "rgba(224, 20, 144, 0.8)",
          "rgba(95, 11, 76, 0.8)",
          "rgba(18, 195, 197, 0.8)",
          "rgba(205, 185, 51, 0.8)",
          "rgba(16, 58, 102, 0.8)",
          "rgba(59, 212, 217, 0.8)",
          "rgba(183, 114, 4, 0.8)",
          "rgba(56, 46, 230, 0.8)",
          "rgba(222, 73, 79, 0.8)",
          "rgba(200, 30, 125, 0.8)",
          "rgba(13, 250, 94, 0.8)",
          "rgba(11, 107, 160, 0.8)"]


def home(request):
    water_data = get_water_dashboard_data()
    gas_data = get_gas_dashboard_data()
    elec_data = get_elec_dashboard_data()
    vmt_data = get_vmt_dashboard_data()

    top_solar_data = SolarEnergy.objects.all().order_by("-production")[:10]

    current_year = datetime.now().year
    top_yearly_solar = SolarEnergy.objects.filter(date_of_production__year=current_year).order_by("-production")[:10]

    return render(request, "data_home.html", {"gas_data": gas_data,
                                              "water_data": water_data,
                                              "elec_data": elec_data,
                                              "vmt_data": vmt_data,
                                              "top_solar_data": top_solar_data,
                                              "top_yearly_solar": top_yearly_solar})


# Data for the dashboard is found in the get_abc_dashboard_data() function
# Data for the individual page is a combination of model properties and classes

def water(request):
    # Get all the years from all the data
    years = get_years_list_from_data(Water.objects.all())
    warning = None

    # Create datasets for all years
    all_yearly_datasets = []
    if years:
        for count, year in enumerate(years):
            new_water_line_data = WaterYear(year, colors[count])
            all_yearly_datasets.append(new_water_line_data)

    # Filter the datasets based on the input, the years the user wants to see
    years_range_from_request = clean_year_range_request(request.GET.get("years"), "Water")
    years_list = convert_years_string_to_years_list(years_range_from_request)

    # Only support 8 years so if there are more, send the user a warning and only send the most recent 8.
    if len(years_list) > 8:
        years_list = years_list[-8:]
        warning = "More than 8 years requested. Only showing most recent 8"

    requested_yearly_datasets = [y for y in all_yearly_datasets if int(y.year) in years_list]

    # Add the average line
    water_avg_line = create_avg_line_data("Water")

    most_recent = Water.objects.latest("service_end_date")

    return render(request, "page.html", {"measurement_units": "Gallons Per Month",
                                         "name": "Water",
                                         "years_range": years_range_from_request,
                                         "yearly_datasets": requested_yearly_datasets,
                                         "avg_line": water_avg_line,
                                         "most_recent": most_recent,
                                         "warning": warning})


def gas(request):
    # Get all the years from all the data
    years = get_years_list_from_data(Gas.objects.all())
    warning = None

    # Create datasets for all years
    all_yearly_datasets = []
    if years:
        for count, year in enumerate(years):
            new_gas_line_data = GasYear(year, colors[count])
            all_yearly_datasets.append(new_gas_line_data)

    # Filter the datasets based on the input, the years the user wants to see
    years_range_from_request = clean_year_range_request(request.GET.get("years"), "Gas")
    years_list = convert_years_string_to_years_list(years_range_from_request)

    # Only support 8 years so if there are more, send the user a warning and only send the most recent 8.
    if len(years_list) > 8:
        years_list = years_list[-8:]
        warning = "More than 8 years requested. Only showing most recent 8"

    requested_yearly_datasets = [y for y in all_yearly_datasets if int(y.year) in years_list]

    # Add the average line
    gas_avg_line = create_avg_line_data("Gas")

    most_recent = Gas.objects.latest("service_end_date")

    return render(request, "page.html", {"measurement_units": "Therms Used",
                                         "name": "Natural Gas",
                                         "years_range": years_range_from_request,
                                         "yearly_datasets": requested_yearly_datasets,
                                         "avg_line": gas_avg_line,
                                         "most_recent": most_recent,
                                         "warning": warning})


def electricity(request):
    # Create a list of years based on the string the user provides or use default
    years_range_request_str = request.GET.get("years")
    years_range_str = clean_year_range_request(years_range_request_str, "Electricity")
    years_list = convert_years_string_to_years_list(years_range_str)

    # Only support 8 years so if there are more, send the user a warning and only send the most recent 8.
    warning = ""
    if len(years_list) > 8:
        years_list = years_list[-8:]
        warning += "More than 8 years requested. Only showing most recent 8.\n"

    # Make a class for each year then remove classes that have no data
    requested_yearly_datasets = [ElecYear(year, colors[count]) for count, year in enumerate(years_list)]
    dataset_lacking_energy_rates = []
    for dataset in list(requested_yearly_datasets):
        if not dataset.readings:
            requested_yearly_datasets.remove(dataset)
            continue
        if dataset.is_lacking_energy_rates() and int(dataset.year) >= 2023:
            dataset_lacking_energy_rates.append(dataset)

    if dataset_lacking_energy_rates:
        warning = f"Some years are lacking energy rates: {str(dataset_lacking_energy_rates)}"

    # Add the average line
    elec_avg_line = create_avg_line_data("Electricity")

    most_recent = Electricity.objects.latest("service_end_date")
    solar_savings_total = f"${sum([s.get_solar_savings_sum() for s in requested_yearly_datasets])}"

    return render(request, "elec.html", {"years_range": years_range_str,
                                         "yearly_datasets": requested_yearly_datasets,
                                         "avg_line": elec_avg_line,
                                         "most_recent": most_recent,
                                         "solar_savings_total": solar_savings_total,
                                         "warning": warning})


def car_miles(request):
    # Get all the years from all the data
    # ex: years = [2020, 2021, 2022, 2023]
    years = get_years_list_from_data(CarMiles.objects.all())
    warning = None

    # Create datasets for all years
    all_yearly_datasets = []
    if years:
        for count, year in enumerate(years):
            new_vmt_line_data = VehicleMilesTraveledYear(year, colors[count])
            all_yearly_datasets.append(new_vmt_line_data)

    # Filter the datasets based on the input, the years the user wants to see
    years_range_from_request = clean_year_range_request(request.GET.get("years"), "CarMiles")
    years_list = convert_years_string_to_years_list(years_range_from_request)

    # Only support 8 years so if there are more, send the user a warning and only send the most recent 8.
    if len(years_list) > 8:
        years_list = years_list[-8:]
        warning = "More than 8 years requested. Only showing most recent 8"

    requested_yearly_datasets = [y for y in all_yearly_datasets if int(y.year) in years_list]

    # Add the average line
    vmt_avg_line = create_avg_line_data("CarMiles")

    return render(request, "miles.html", {"vmt_data_per_years_given":
                                              get_measurement_data_from_years("CarMiles", years_range_from_request),
                                          "years_range": years_range_from_request,
                                          "yearly_datasets": requested_yearly_datasets,
                                          "avg_line": vmt_avg_line,
                                          "warning": warning})


def export_csv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="export.csv"'},
    )

    queryset = Electricity.objects.all()
    model = queryset.model
    model_fields = model._meta.fields + model._meta.many_to_many
    field_names = [field.name for field in model_fields]

    writer = csv.writer(response, delimiter=";")
    writer.writerow(field_names)
    for row in queryset:
        values = []
        for field in field_names:
            value = getattr(row, field)
            if callable(value):
                try:
                    value = value() or ''
                except Exception as e:
                    value = 'Error retrieving value'
            if value is None:
                value = ''
            values.append(value)
        writer.writerow(values)

    return response

@login_required(login_url="/admin")
def upload_files(request):
    if request.method == "POST":
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, "No file uploaded.")
            return redirect("/data/upload/")

        if not uploaded_file.name.lower().endswith('.pdf'):
            messages.error(request, "Only PDF files are allowed.")
            return redirect("/data/upload/")

        # Save to a temporary location
        temp_path = default_storage.save(f"temp/{uploaded_file.name}", uploaded_file)
        temp_file_path = os.path.join(settings.MEDIA_ROOT, temp_path)

        try:
            # Get all data from the pdf
            parsed_data = extract_pdf_data_for_preview(temp_file_path)

            # Calculate $ saved by solar
            instance = Electricity(
                bill_date=date.fromisoformat(parsed_data["billing_date"]),
                service_start_date=date.fromisoformat(parsed_data["start_date"]),
                service_end_date=date.fromisoformat(parsed_data["end_date"]),
                kWh_usage=parsed_data["electricity_usage_kwh"],
                solar_amt_sent_to_grid=parsed_data["energy_delivered_to_grid"],
                net_metering_credit=parsed_data["carried_forward_balance"],
            )
            calculated_money_saved_by_solar = instance.get_money_saved_by_solar
            parsed_data["calculated_money_saved_by_solar"] = str(calculated_money_saved_by_solar)

        except Exception as e:
            messages.error(request, "Failed to process PDF.")
            return redirect("/data/upload/")

        # Save parsed data in session (or use cache/hidden form fields)
        request.session['parsed_data'] = parsed_data
        request.session['temp_file_path'] = temp_file_path

        return redirect("/data/preview")

    return render(request, "upload.html")

@login_required(login_url="/admin")
@require_http_methods(["GET", "POST"])
def preview_pdf(request):
    parsed_data = request.session.get('parsed_data')
    temp_file_path = request.session.get('temp_file_path')

    if not parsed_data or not temp_file_path:
        messages.error(request, "Missing data. Please upload again.")
        return redirect("/data/upload/")

    if request.method == "POST":
        if 'cancel' in request.POST:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            request.session.pop('parsed_data', None)
            request.session.pop('temp_file_path', None)
            return redirect("/data/upload/")


        elif 'save' in request.POST:
            try:
                model_data = extract_pdf_data_for_saving(temp_file_path)
                electricity_instance = Electricity.objects.create(
                    bill_date=model_data["billing_date"],
                    service_start_date=model_data["start_date"],
                    service_end_date=model_data["end_date"],
                    kWh_usage=model_data["electricity_usage_kwh"],
                    solar_amt_sent_to_grid=model_data["energy_delivered_to_grid"],
                    net_metering_credit=model_data["carried_forward_balance"]
                )

                if os.path.exists(temp_file_path):
                    with open(temp_file_path, 'rb') as f:
                        filename = Path(temp_file_path).name
                        electricity_instance.uploaded_pdf.save(filename, File(f), save=True)

                messages.success(request, "Data saved.")
                return redirect("/data/upload/")

            except (KeyError, OSError) as e:
                messages.error(request, f"Error saving data: {e}")
                return redirect("/data/upload/")

            finally:
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except Exception as e:
                        logger.warning(f"Could not delete temp file: {e}")
                request.session.pop('parsed_data', None)
                request.session.pop('temp_file_path', None)

    return render(request, "preview.html", {"data": parsed_data})