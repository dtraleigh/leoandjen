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
        # Miles-to-next-month for every reading, computed once instead of per row.
        self.miles_by_pk = CarMiles.get_miles_per_month_map()
        self.data_points = self.get_data_points()

    def __repr__(self):
        return f"VMT dataset for {self.year}"

    def get_data_points(self):
        data_points = []
        all_vmt_data = list(CarMiles.objects.order_by("reading_date"))
        if not all_vmt_data:
            return data_points
        # We must skip the most recent datapoint as you can't calculate the VMT miles from it
        most_recent = all_vmt_data[-1]

        for reading in all_vmt_data:
            if reading.reading_date.year != int(self.year):
                continue
            if reading == most_recent:
                continue
            data_points.append({
                "month_number": reading.reading_date.month,
                "month_str": month_strings_abbr[reading.reading_date.month - 1],
                "value": self.miles_by_pk[reading.pk],
            })

        return data_points

    @property
    def get_total_miles(self):
        return sum(miles for reading in self.readings
                   if (miles := self.miles_by_pk.get(reading.pk)) is not None)

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
