import csv
import logging
from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render

from data.functions import *
from data.models import *
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

    return render(request, "data_home.html", {"gas_data": gas_data,
                                              "water_data": water_data,
                                              "elec_data": elec_data,
                                              "vmt_data": vmt_data,
                                              "top_solar_data": top_solar_data})


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
