from calendar import monthrange
from datetime import datetime
from decimal import Decimal

from django.db.models import Q, Sum

from data.models import Electricity, SolarEnergy


class ElecYear:
    def __init__(self, year, color):
        from data.functions import get_measurement_data_from_years

        self.title = "Electricity"
        self.measurement = "Kilowatt hours used (house)"
        self.year = str(year)
        self.color = color
        self.chart_type = "line"
        self.borderWidth = 2
        self.latest_data_point = Electricity.objects.latest("service_end_date")
        # A reading is a model object from the database
        # Get bills with a service_start_date in this year
        self.readings = get_measurement_data_from_years("Electricity", str(year))
        self.data_points = self.get_data_points()

    def __repr__(self):
        return f"Elec dataset for {self.year}"

    def get_data_points(self):
        from data.functions import month_strings_abbr

        # Create a list of dictionaries like
        # [{'month_number': '1', 'month_str': 'Jan', 'value': 956}, .....
        # Improve get_data_points by returning the value = daily usage for each day in this year
        data_points = []
        this_years_elec_data = Electricity.objects.filter(Q(bill_date__year=self.year) |
                                                          Q(service_start_date__year=self.year) |
                                                          Q(service_end_date__year=self.year))

        # Create the generic list of data, one for each month
        for month in range(1, 13):
            data_point = {"month_number": month,
                          "month_str": month_strings_abbr[month - 1],
                          "days_in_month": monthrange(int(self.year), month)[1],
                          "value": Decimal("0.0"),
                          "solar_produced": Decimal("0.0"),
                          "solar_sent_to_grid": Decimal("0.0"),
                          "grid_energy_consumed": Decimal("0.0"),
                          "daily_consumption": None}
            data_points.append(data_point)

        # Now go through each bill and update the months value
        for bill in this_years_elec_data:
            for month in data_points:
                month["solar_sent_to_grid"] += round(self.get_months_solar_sent_to_grid(bill, month["month_number"]), 2)
                month["grid_energy_consumed"] = round(month["grid_energy_consumed"] +
                                                      self.get_months_grid_energy_consumed(bill, month["month_number"]),
                                                      2)

        # Remove future months
        for month in list(data_points):
            if month["month_number"] > self.latest_data_point.service_end_date.month \
                    and int(self.year) >= self.latest_data_point.service_end_date.year:
                data_points.remove(month)

        # For these two, no need to go through each bill
        for month in data_points:
            month["solar_produced"] += self.get_total_solar_produced_by_month(month["month_number"])

            # Total House energy = Grid Energy Consumed + Solar Produced - Solar energy sent to grid
            month["value"] += round(
                month["grid_energy_consumed"] + month["solar_produced"] - month["solar_sent_to_grid"], 2)

            # Daily consumption per month is month["value"] / month["days_in_month"]
            month["daily_consumption"] = round(month["value"] / month["days_in_month"], 2)

        return data_points

    def get_ytd_total(self, last_month=datetime.now().month - 1):
        # YTD should be total between Jan 1 and first of the current month
        # - Since we get data in chunks (the bills), not worrying about YTD daily values
        # - Therefore, YTD range is from Jan 1 up to current_month 1
        datapoints = self.get_data_points()

        ytd_total = Decimal("0.0")
        for datapoint in datapoints:
            if datapoint["month_number"] <= last_month:
                ytd_total += datapoint["value"]

        return ytd_total

    def get_total_solar_produced_by_month(self, month):
        solar_days = SolarEnergy.objects.filter(date_of_production__year=self.year,
                                                date_of_production__month=month)
        # return as kilowatts hours
        if solar_days:
            result = solar_days.aggregate(Sum("production"))["production__sum"] / 1000
        else:
            result = Decimal("0.00")

        return Decimal(result).quantize(Decimal("1.00"))

    def get_months_solar_sent_to_grid(self, bill, month):
        num_days_of_data_in_month = bill.get_number_of_days_in_month(month, self.year)
        if num_days_of_data_in_month > 0:
            return bill.get_daily_solar_send * num_days_of_data_in_month
        return 0

    def get_months_grid_energy_consumed(self, bill, month):
        num_days_of_data_in_month = bill.get_number_of_days_in_month(month, self.year)
        if num_days_of_data_in_month > 0:
            return bill.get_daily_grid_usage * num_days_of_data_in_month
        return 0

    def create_solar_savings_table_data(self):
        # Keep it simple for now, create a list like ["date range str", "$12.34"]
        readings = [b for b in self.readings]
        if readings:
            start = readings[0].service_start_date
            end = readings[-1].service_end_date
            date_str = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"

            solar_savings = sum([t.calculated_money_saved_by_solar for t in self.readings])
            savings_str = f"${solar_savings}"

            return [date_str, savings_str]
        return None

    def get_solar_savings_sum(self):
        if self.readings:
            return sum([t.calculated_money_saved_by_solar for t in self.readings])
        return None

    def get_readings_kwh_total(self):
        if self.readings:
            return sum([t.kWh_usage for t in self.readings])
        return None

    def get_solar_produced_total(self):
        if self.readings:
            return round(sum([t.get_total_solar_produced for t in self.readings]), 3)
        return None

    def get_solar_sent_to_grid_total(self):
        if self.readings:
            return sum([t.solar_amt_sent_to_grid for t in self.readings])
        return None

    def get_total_house_consumed(self):
        # Total House energy = grid_energy_consumed + solar_produced - solar_energy_sent_to_grid_kwh
        if self.readings:
            return round(
                self.get_readings_kwh_total() + self.get_solar_produced_total() - self.get_solar_sent_to_grid_total(),
                3)
        return None

    def get_solar_bar_chart_dataset(self):
        solar_bar_dataset = f"{{label:'none'," \
                            f"type:'bar'," \
                            f"borderColor:'{self.color}'," \
                            f"borderWidth:'{self.borderWidth}'," \
                            f"data:{[float(x['solar_produced']) for x in self.get_data_points()]}}}"

        return solar_bar_dataset
