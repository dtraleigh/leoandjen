from datetime import datetime

from django.db.models import Q

from data.models import Water


class WaterYear:
    def __init__(self, year, color):
        from data.functions import get_measurement_data_from_years

        self.title = "Water"
        self.short_title = "Water"
        self.measurement = "Gallons / Month"
        self.year = str(year)
        self.color = color
        self.chart_type = "line"
        self.borderWidth = 2
        self.latest_data_point = Water.objects.latest("service_end_date")
        self.readings = get_measurement_data_from_years("Water", str(year))
        self.data_points = self.get_data_points()

    def __repr__(self):
        return f"Water dataset for {self.year}"

    def get_data_points(self):
        from data.functions import month_strings_abbr

        # Create a list of dictionaries like
        # [{'month_number': '1', 'month_str': 'Jan', 'value': 956}, .....
        # Improve get_data_points by returning the value = daily usage for each day in this year
        data_points = []
        this_years_water_data = Water.objects.filter(Q(bill_date__year=self.year) |
                                                     Q(service_start_date__year=self.year) |
                                                     Q(service_end_date__year=self.year))

        # Create the generic list of data, one for each month
        for month in range(1, 13):
            data_point = {"month_number": month,
                          "month_str": month_strings_abbr[month - 1],
                          "value": 0}
            data_points.append(data_point)

        # Now go through each bill and update the months value
        for bill in this_years_water_data:
            for month in data_points:
                month["value"] = round(month["value"] + self.get_months_water_consumed(bill, month["month_number"]), 2)

        # Remove future months
        for month in list(data_points):
            if month["month_number"] > self.latest_data_point.service_end_date.month \
                    and int(self.year) >= self.latest_data_point.service_end_date.year:
                data_points.remove(month)

        return data_points

    def get_ytd_total(self):
        # Query the latest month from the Water table here
        try:
            latest_month = Water.objects.latest("service_end_date").service_end_date.month
        except Water.DoesNotExist:
            # Handle the case where there are no records in Water
            return 0

        # YTD should be total between Jan 1 and first of the current month
        # - Since we get data in chunks (the bills), not worrying about YTD daily values
        # - Therefore, YTD range is from Jan 1 up to current_month or the latest bill we have
        datapoints = self.get_data_points()

        ytd_total = 0
        for datapoint in datapoints:
            if datapoint["month_number"] <= latest_month:
                ytd_total += datapoint["value"]

        return ytd_total

    def get_months_water_consumed(self, bill, month):
        num_days_of_data_in_month = bill.get_number_of_days_in_month(month, self.year)
        if num_days_of_data_in_month > 0:
            return bill.avg_gallons_per_day * num_days_of_data_in_month
        return 0
