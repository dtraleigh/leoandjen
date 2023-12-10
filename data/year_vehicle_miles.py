from data.functions import *
from data.models import CarMiles


class VehicleMilesTraveledYear:
    def __init__(self, year, color):
        self.title = "Vehicle Miles Traveled"
        self.short_title = "VMT"
        self.measurement = "Miles / Month"
        self.year = str(year)
        self.color = color
        self.chart_type = "line"
        self.borderWidth = 2
        self.latest_data_point = CarMiles.objects.latest("reading_date")
        self.readings = get_measurement_data_from_years("CarMiles", str(year))
        self.data_points = self.get_data_points()

    def __repr__(self):
        return f"VMT dataset for {self.year}"

    def get_data_points(self):
        data_points = []
        all_vmt_data = CarMiles.objects.all()

        for reading in all_vmt_data:
            data_point = {}
            if reading.reading_date.year == int(self.year):
                # 1 to 12
                data_point["month_number"] = reading.reading_date.month
                data_point["month_str"] = month_strings_abbr[int(data_point["month_number"]) - 1]
                data_point["value"] = reading.get_miles_per_month

                # We must skip the most recent datapoint as you can't calculate the VMT miles from it
                if reading != all_vmt_data.order_by("reading_date").last():
                    data_points.append(data_point)

        return data_points

    @property
    def get_total_miles(self):
        return sum([datapoint.get_miles_per_month for datapoint in self.readings if
                    datapoint.get_miles_per_month is not None])

    def get_ytd_miles(self, custom_most_recent=None):
        """Since data is put in manually, "date" in YTD is the most recent datapoint.
         Use a default value, the most recent datapoint, so we know which year and month is current
         We can override this for test purposes.
        """
        try:
            if custom_most_recent:
                most_recent_odometer_reading = custom_most_recent
            else:
                most_recent_odometer_reading = CarMiles.objects.all().latest("reading_date")
        except Exception:
            return 0

        # Get the same month's datapoint of this year
        this_years_YTD_odometer_reading = CarMiles.objects.get(reading_date__year=self.year,
                                                               reading_date__month=most_recent_odometer_reading.reading_date.month).odometer_reading

        # Get the January datapoint of this year
        jan_this_years_odometer_reading = CarMiles.objects.get(reading_date__year=self.year,
                                                               reading_date__month=1).odometer_reading

        return this_years_YTD_odometer_reading - jan_this_years_odometer_reading
