from datetime import datetime

from django.db.models import Q

from data.models import Gas


class GasYear:
    def __init__(self, year, color):
        from data.functions import get_measurement_data_from_years

        self.title = "Natural Gas"
        self.short_title = "Gas"
        self.measurement = "Therms per month"
        self.year = str(year)
        self.color = color
        self.chart_type = "line"
        self.borderWidth = 2
        self.latest_data_point = Gas.objects.latest("service_end_date")
        self.readings = get_measurement_data_from_years("Gas", str(year))
        self.data_points = self.get_data_points()

    def __repr__(self):
        return f"Gas dataset for {self.year}"

    def get_data_points(self):
        from data.functions import month_strings_abbr

        # Create a list of dictionaries like
        # [{'month_number': '1', 'month_str': 'Jan', 'value': 956}, .....
        # Improve get_data_points by returning the value = daily usage for each day in this year
        data_points = []
        this_years_gas_data = Gas.objects.filter(Q(bill_date__year=self.year) |
                                                 Q(service_start_date__year=self.year) |
                                                 Q(service_end_date__year=self.year))

        # Create the generic list of data, one for each month
        for month in range(1, 13):
            data_point = {"month_number": month,
                          "month_str": month_strings_abbr[month - 1],
                          "value": 0}
            data_points.append(data_point)

        # Now go through each bill and update the months value
        for bill in this_years_gas_data:
            for month in data_points:
                month["value"] = round(month["value"] + self.get_months_gas_consumed(bill, month["month_number"]), 2)

        # Remove future months
        for month in list(data_points):
            if month["month_number"] > self.latest_data_point.service_end_date.month \
                    and int(self.year) >= self.latest_data_point.service_end_date.year:
                data_points.remove(month)

        return data_points

    def get_ytd_total(self):
        # Query the latest month from the Gas table here
        try:
            latest_month = Gas.objects.latest("service_end_date").service_end_date.month
        except Gas.DoesNotExist:
            # Handle the case where there are no records in Gas
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

    def get_months_gas_consumed(self, bill, month):
        num_days_of_data_in_month = bill.get_number_of_days_in_month(month, self.year)
        if num_days_of_data_in_month > 0:
            return bill.get_daily_gas_usage * num_days_of_data_in_month
        return 0
