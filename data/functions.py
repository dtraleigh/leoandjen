import calendar
import operator
from datetime import datetime
from functools import reduce

from django.apps import apps
from django.core.exceptions import FieldError
from django.db.models import Q

from data.models import *
from data.year_elec import ElecYear
from data.year_gas import GasYear
from data.year_water import WaterYear

measurement_units = {
    "Water": "avg_gallons_per_day",
    "Electricity": "kWh_usage",
    "Gas": "therms_usage"
}

currentYear = datetime.now().year

month_strings_abbr = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]


def get_years_list_from_data(object_data):
    """Returns a sorted list of years. Given input as some queryset of data, give me
    all the years across the data points.
    """
    if object_data:
        data_type = type(object_data[0]).__name__
        dataset_years = []

        for datapoint in object_data:
            if data_type != "CarMiles":
                dataset_years.append(datapoint.service_start_date.year)
                dataset_years.append(datapoint.service_end_date.year)
            else:
                dataset_years.append(datapoint.reading_date.year)
                dataset_years.append(datapoint.reading_date.year)

        dataset_years = list(set(dataset_years))
        dataset_years.sort()

        return dataset_years
    else:
        return None


def get_midpoint_of_dates(date1, date2):
    return date1 + (date2 - date1) / 2


def clean_year_range_request(years_range, class_name):
    """
    By default, return this year and last 2 years as a string. Ex. "2020-2022"
    If, no input given, use default,
    elif, account for special keywords
    else, just return the given string
    """
    data_class = apps.get_model(app_label="data", model_name=class_name)

    if not years_range:
        return str(datetime.now().year - 2) + "-" + str(datetime.now().year)
    elif years_range.lower() == "all":
        try:
            return f"{str(data_class.objects.earliest('service_start_date').service_start_date.year)}-" \
                   f"{str(data_class.objects.latest('service_start_date').service_start_date.year)}"
        except FieldError:
            return f"{str(data_class.objects.earliest('reading_date').reading_date.year)}-" \
                   f"{str(data_class.objects.latest('reading_date').reading_date.year)}"
    elif years_range.replace(" ", "")[-1] == "+":
        starting_year = years_range[:4]
        try:
            return f"{starting_year}-{str(data_class.objects.latest('service_start_date').service_start_date.year)}"
        except FieldError:
            return f"{starting_year}-{str(data_class.objects.latest('reading_date').reading_date.year)}"
    return years_range.replace(" ", "")


def convert_years_string_to_years_list(years_string):
    """Convert a string to a list. Ex. "2020-2022"  to [2020, 2021, 2022]"""
    if "-" in years_string:
        year_split = years_string.split("-")
        start = int(year_split[0])
        end = int(year_split[1])
        return [y for y in range(start, end + 1)]
    elif "," in years_string:
        return [int(y) for y in years_string.split(",")]
    else:
        try:
            return [int(years_string)]
        except ValueError:
            return []


def get_number_of_days_in_month(datapoint):
    # Take a measurement and see what month it takes place in, then return the number of days in that month
    # To account for possible service start dates and end dates in different years, use the midpoint
    month = get_midpoint_of_dates(datapoint.service_start_date, datapoint.service_end_date).month
    year = get_midpoint_of_dates(datapoint.service_start_date, datapoint.service_end_date).year

    return calendar.monthrange(year, month)[1]


def get_average(lst):
    try:
        return sum(lst) / len(lst)
    except ZeroDivisionError:
        return 0


def get_measurement_data_from_years(data_name, years_range):
    """Returns a list of datapoints per the years given in the range. Sorting is model default
    The years_range is the string from the request. Ex. "2020-2022"
    """
    data_class = apps.get_model(app_label="data", model_name=data_name)
    # years_range = str(years_range).replace(" ", "")

    if data_name != "CarMiles":
        if "-" in years_range:
            return data_class.objects.filter(service_start_date__year__gte=years_range.split("-")[0],
                                             service_start_date__year__lte=years_range.split("-")[1])
        elif "," in years_range:
            years = years_range.split(",")
            return data_class.objects.filter(reduce(operator.or_,
                                                    (Q(service_start_date__year__contains=y) for y in years)))
        elif "-" not in years_range and "," not in years_range:
            try:
                return data_class.objects.filter(service_start_date__year=years_range)
            except ValueError:
                return None
    else:
        if "-" in years_range:
            return CarMiles.objects.filter(reading_date__year__gte=years_range.split("-")[0],
                                           reading_date__year__lte=years_range.split("-")[1])
        elif "," in years_range:
            years = years_range.split(",")
            return CarMiles.objects.filter(reduce(operator.or_,
                                                  (Q(reading_date__year__contains=y) for y in years)))
        elif "-" not in years_range and "," not in years_range:
            try:
                return CarMiles.objects.filter(reading_date__year=years_range)
            except ValueError:
                return None


def create_avg_line_data(class_name):
    data_class = apps.get_model(app_label="data", model_name=class_name)

    try:
        recent_year = data_class.objects.latest("service_start_date").service_start_date.year
    except FieldError:
        recent_year = data_class.objects.latest("reading_date").reading_date.year

    try:
        first_year = data_class.objects.earliest("service_start_date").service_start_date.year
    except FieldError:
        first_year = data_class.objects.earliest("reading_date").reading_date.year

    avg_years_line_data = {"label": f"Average ({str(first_year)}-{str(recent_year - 1)})",
                           "color": "rgba(22, 51, 73, 0.1)",
                           "borderWidth": 5,
                           "data_points": []}

    years = [y for y in range(first_year, recent_year)]

    if class_name != "CarMiles":
        if class_name == "Water":
            yearly_objects = [WaterYear(year, "") for year in years]
        elif class_name == "Gas":
            yearly_objects = [GasYear(year, "") for year in years]
        elif class_name == "Electricity":
            yearly_objects = [ElecYear(year, "") for year in years]

        for month in range(1, 13):
            data_point = {}
            month_data = []
            for year in yearly_objects:
                datapoints = year.get_data_points()
                month_data.append([m["value"] for m in datapoints if m["month_number"] == month][0])

            data_point["month_number"] = month
            data_point["month_str"] = month_strings_abbr[int(data_point["month_number"]) - 1]
            data_point["value"] = get_average(month_data)
            avg_years_line_data["data_points"].append(data_point)

        return avg_years_line_data
    else:
        # Data from first_year to recent_year - 1
        all_data_for_avg_line = data_class.objects.filter(reading_date__year__gte=first_year,
                                                          reading_date__year__lt=recent_year)

        # Go through each month of each year
        for month in range(1, 13):
            data_point = {}

            month_data_objects = [x for x in all_data_for_avg_line if x.reading_date.month == month]
            month_data = [y.get_miles_per_month for y in month_data_objects]
            avg = get_average(month_data)
            # 1 to 12
            data_point["month_number"] = month
            data_point["month_str"] = month_strings_abbr[int(data_point["month_number"]) - 1]
            data_point["value"] = avg
            avg_years_line_data["data_points"].append(data_point)

        return avg_years_line_data


def get_YTD_range_label(some_data):
    """Return a string with the beginning of the year's month and most recent month of data from
    the data_class - 1 (there are cases where the most recent month has not enough data yet."""
    try:
        data_type = type(some_data[0]).__name__
        data_class = apps.get_model(app_label="data", model_name=data_type)
    except IndexError:
        return None

    if data_type != "CarMiles":
        latest_month_of_data = data_class.objects.filter(bill_date__isnull=False).latest("bill_date")
        return f"{month_strings_abbr[0]} 1 - {month_strings_abbr[latest_month_of_data.service_end_date.month - 1]} {latest_month_of_data.service_end_date.day}"
    else:
        latest_month_of_data = data_class.objects.filter(reading_date__isnull=False).latest("reading_date")
        latest_month = latest_month_of_data.reading_date.month
        return f"{month_strings_abbr[0]} - {month_strings_abbr[latest_month - 2]}"


def get_trending_info(ytd_total, all_ytd_avg):
    # if the year-to-date total is below the year-to-date average across all previous years
    # then we say we are trending downward. Else, we are up.
    try:
        if ytd_total < all_ytd_avg:
            return "down"
        else:
            return "up"
    except TypeError:
        return None


def get_gas_dashboard_data(current_date=datetime.now()):
    # initial data structure
    data = {
        "ytd_total": None,
        "prev_ytd": None,
        "all_ytd_avg": None,
        "ytd_range": get_YTD_range_label(Gas.objects.all()),
        "overall_trend": None,
        "title": None,
        "measurement": None
    }

    start = list(set([g.service_start_date.year for g in Gas.objects.all()]))
    end = list(set([g.service_end_date.year for g in Gas.objects.all()]))
    all_gas_years = list(set(start + end + [current_date.year]))
    all_gas_years.sort()
    gas_year_objects = [GasYear(year, "") for year in all_gas_years]

    data["title"] = "Natural Gas"
    data["measurement"] = "Therms per month"

    data["ytd_total"] = gas_year_objects[-1].get_ytd_total()
    data["prev_ytd"] = gas_year_objects[-2].get_ytd_total()
    data["all_ytd_avg"] = round(get_average([y.get_ytd_total() for y in gas_year_objects[:-1]]))

    # If data["ytd_total"] < data["all_ytd_avg"] then down
    data["overall_trend"] = get_trending_info(data["ytd_total"], data["all_ytd_avg"])

    return data


def get_water_dashboard_data(current_date=datetime.now()):
    # initial data structure
    data = {
        "ytd_total": None,
        "prev_ytd": None,
        "all_ytd_avg": None,
        "ytd_range": get_YTD_range_label(Water.objects.all()),
        "overall_trend": None,
        "title": None,
        "measurement": None
    }

    start = list(set([w.service_start_date.year for w in Water.objects.all()]))
    end = list(set([w.service_end_date.year for w in Water.objects.all()]))
    all_water_years = list(set(start + end + [current_date.year]))
    all_water_years.sort()
    water_year_objects = [WaterYear(year, "") for year in all_water_years]

    data["title"] = "Water"
    data["measurement"] = "Gallons per month"

    data["ytd_total"] = water_year_objects[-1].get_ytd_total()
    data["prev_ytd"] = water_year_objects[-2].get_ytd_total()
    data["all_ytd_avg"] = round(get_average([y.get_ytd_total() for y in water_year_objects[:-1]]))

    # If data["ytd_total"] < data["all_ytd_avg"] then down
    data["overall_trend"] = get_trending_info(data["ytd_total"], data["all_ytd_avg"])

    return data


def get_elec_dashboard_data(current_date=datetime.now()):
    # initial data structure
    data = {
        "ytd_total": None,
        "prev_ytd": None,
        "all_ytd_avg": None,
        "ytd_range": get_YTD_range_label(Electricity.objects.all()),
        "overall_trend": None,
        "title": "Electricity",
        "measurement": "Kilowatt hours used (Grid)"
    }

    # Get a list of years that spans all elec data
    start = list(set([e.service_start_date.year for e in Electricity.objects.all()]))
    end = list(set([e.service_end_date.year for e in Electricity.objects.all()]))
    # We need a class for the current year even if we don't have any data for it
    # This breaks if you go an entire year without entering data but just don't do that. :)
    all_elec_years = list(set(start + end + [current_date.year]))
    all_elec_years.sort()
    # Ex: [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]

    # For each year, create an ElecYear class
    elec_year_objects = [ElecYear(year, "") for year in all_elec_years]

    data["prev_ytd"] = elec_year_objects[-2].get_ytd_total()
    data["all_ytd_avg"] = round(get_average([y.get_ytd_total() for y in elec_year_objects[:-1]]))

    # If data["ytd_total"] < data["all_ytd_avg"] then down
    data["overall_trend"] = get_trending_info(data["ytd_total"], data["all_ytd_avg"])

    return data


def get_vmt_dashboard_data():
    # initial data structure
    data = {"ytd_total": get_car_miles_ytd_total(),
            "prev_ytd": get_car_miles_prev_ytd(),
            "all_ytd_avg": get_car_miles_all_ytd_avg(),
            "ytd_range": get_YTD_range_label(CarMiles.objects.all()),
            "overall_trend": None,
            "title": "Vehicle Miles Traveled",
            "measurement": "Miles / Month"
            }

    # If data["ytd_total"] < data["all_ytd_avg"] then down
    data["overall_trend"] = get_trending_info(data["ytd_total"], data["all_ytd_avg"])

    return data


def get_car_miles_ytd_total(custom_most_recent=None):
    try:
        if custom_most_recent:
            most_recent_odometer_reading = custom_most_recent
        else:
            most_recent_odometer_reading = CarMiles.objects.all().latest("reading_date")
    except Exception:
        return 0

    return most_recent_odometer_reading.odometer_reading - \
        CarMiles.objects.get(reading_date__month=1,
                             reading_date__year=most_recent_odometer_reading.reading_date.year).odometer_reading


def get_car_miles_prev_ytd(custom_most_recent=None):
    try:
        if custom_most_recent:
            most_recent_odometer_reading = custom_most_recent
        else:
            most_recent_odometer_reading = CarMiles.objects.all().latest("reading_date")
    except Exception:
        return 0

    return CarMiles.objects.get(reading_date__month=most_recent_odometer_reading.reading_date.month,
                                reading_date__year=most_recent_odometer_reading.reading_date.year - 1).odometer_reading - \
        CarMiles.objects.get(reading_date__month=1,
                             reading_date__year=most_recent_odometer_reading.reading_date.year - 1).odometer_reading


def get_car_miles_all_ytd_avg(custom_most_recent=None):
    """ The average YTD from previous years"""
    try:
        if custom_most_recent:
            most_recent_odometer_reading = custom_most_recent
        else:
            most_recent_odometer_reading = CarMiles.objects.all().latest("reading_date")
    except Exception:
        return 0

    most_recent_odometer_reading_month = most_recent_odometer_reading.reading_date.month
    most_recent_odometer_reading_year = most_recent_odometer_reading.reading_date.year
    all_vmt_data_YTD = CarMiles.objects.filter(reading_date__month__lte=most_recent_odometer_reading_month,
                                               reading_date__year__lte=most_recent_odometer_reading_year)
    years = list(set([a.reading_date.year for a in all_vmt_data_YTD]))
    years.sort()
    del years[-1]

    prev_years_values = []
    for year in years:
        data = CarMiles.objects.filter(reading_date__year=year,
                                       reading_date__month__lte=most_recent_odometer_reading_month)
        prev_years_values.append(
            data.latest("reading_date").odometer_reading - data.earliest("reading_date").odometer_reading)

    return round(get_average(prev_years_values))


def get_days_energy_charge_per_kwh(month, day, year):
    dt_obj = datetime(year, month, day)
    rate_schedule = ElectricRateSchedule.objects.get(schedule_start_date__lte=dt_obj, schedule_end_date__gte=dt_obj)

    return rate_schedule.energy_charge_per_kwh


def get_days_storm_recover_cost_per_kwh(month, day, year):
    dt_obj = datetime(year, month, day)
    rate_schedule = ElectricRateSchedule.objects.get(schedule_start_date__lte=dt_obj, schedule_end_date__gte=dt_obj)

    return rate_schedule.storm_recover_cost_per_kwh
