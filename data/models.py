import decimal
from decimal import Decimal
from django.db import models
from datetime import timedelta


class Water(models.Model):
    submit_date = models.DateField(auto_now_add=True)
    bill_date = models.DateField(blank=True, null=True)
    service_start_date = models.DateField()
    service_end_date = models.DateField()
    avg_gallons_per_day = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name_plural = "Water"
        ordering = ["service_start_date"]

    def get_cname(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.service_start_date} to {self.service_end_date} ({self.id})"

    @property
    def get_number_of_days(self):
        # data includes the end and starts so let's add 1
        return self.service_end_date - self.service_start_date + timedelta(days=1)

    def get_number_of_days_in_month(self, month, year):
        year = int(year)
        day_count = 0
        list_of_dates = [self.service_start_date + timedelta(days=x) for x in
                         range((self.service_end_date - self.service_start_date).days)]
        # above does not include self.service_end_date itself
        # list_of_dates.append(self.service_end_date) <-- No need for Water
        for date in list_of_dates:
            if date.month == month and date.year == year:
                day_count += 1
        return day_count


class SolarEnergy(models.Model):
    submit_date = models.DateField(auto_now_add=True)
    date_of_production = models.DateField()
    production = models.IntegerField("Watts produced")

    class Meta:
        verbose_name_plural = "Solar Energy"
        ordering = ["date_of_production"]

    def get_cname(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.date_of_production} ({self.id})"


class Electricity(models.Model):
    submit_date = models.DateField(auto_now_add=True)
    bill_date = models.DateField(blank=True, null=True)
    service_start_date = models.DateField()
    service_end_date = models.DateField()
    kWh_usage = models.IntegerField("Grid Energy Consumed")
    solar_amt_sent_to_grid = models.IntegerField("Solar Sent to Grid")
    net_metering_credit = models.IntegerField("Net Metering Balance", default=0)
    energy_charge_per_kwh = models.DecimalField(max_digits=9,
                                                decimal_places=8,
                                                blank=True, null=True,
                                                verbose_name="Energy Charge per kWh",
                                                default=Decimal("0.11815"))
    storm_recover_cost_per_kwh = models.DecimalField(max_digits=9,
                                                     decimal_places=8,
                                                     blank=True, null=True,
                                                     verbose_name="Storm Recovery Cost per kWh",
                                                     default=Decimal("0.00219"))

    class Meta:
        verbose_name_plural = "Electricity"
        ordering = ["service_start_date"]

    def get_cname(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.service_start_date} to {self.service_end_date} ({self.id})"

    @property
    def get_number_of_days(self):
        # data includes the end and starts so let's add 1
        return self.service_end_date - self.service_start_date + timedelta(days=1)

    @property
    def get_daily_grid_usage(self):
        result = self.kWh_usage / self.get_number_of_days.days
        return Decimal(result).quantize(Decimal("1.00"))

    @property
    def get_daily_solar_send(self):
        result = self.solar_amt_sent_to_grid / self.get_number_of_days.days
        return Decimal(result).quantize(Decimal("1.00"))

    def get_number_of_days_in_month(self, month, year):
        year = int(year)
        day_count = 0
        list_of_dates = [self.service_start_date + timedelta(days=x) for x in
                         range((self.service_end_date - self.service_start_date).days)]
        # above does not include self.service_end_date itself
        list_of_dates.append(self.service_end_date)
        for date in list_of_dates:
            if date.month == month and date.year == year:
                day_count += 1
        return day_count

    @property
    def get_total_solar_produced(self):
        solar_days = SolarEnergy.objects.filter(date_of_production__gte=self.service_start_date,
                                                date_of_production__lte=self.service_end_date)
        # return as kilowatts hours
        return sum([day.production for day in solar_days]) / 1000

    @property
    def get_bill_before_this_one(self):
        bills = Electricity.objects.all()
        this_bills_index = [x for x in bills].index(self)
        return [x for x in bills][this_bills_index - 1]

    @property
    def get_money_saved_by_solar(self):
        # Returns as a Decimal rounded to 2 DP
        decimal.getcontext().rounding = decimal.ROUND_HALF_UP

        credited_solar = self.get_bill_before_this_one.net_metering_credit + self.solar_amt_sent_to_grid
        billed_kWh = self.kWh_usage - credited_solar
        if billed_kWh < 0:
            this_bills_kWh_saved = self.kWh_usage
        else:
            this_bills_kWh_saved = credited_solar

        try:
            savings = (this_bills_kWh_saved * self.energy_charge_per_kwh) + \
                  (this_bills_kWh_saved * self.storm_recover_cost_per_kwh)
            return savings.quantize(Decimal("1.00"))
        except TypeError:
            return Decimal("0.00")


class Gas(models.Model):
    submit_date = models.DateField(auto_now_add=True)
    bill_date = models.DateField(blank=True, null=True)
    service_start_date = models.DateField()
    service_end_date = models.DateField()
    therms_usage = models.IntegerField()

    class Meta:
        verbose_name_plural = "Natural Gas"
        ordering = ["service_start_date"]

    def get_cname(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.service_start_date} to {self.service_end_date} ({self.id})"

    @property
    def get_number_of_days(self):
        # data includes the end and starts so let's add 1
        return self.service_end_date - self.service_start_date + timedelta(days=1)

    @property
    def get_daily_gas_usage(self):
        return round(self.therms_usage / self.get_number_of_days.days, 2)

    def get_number_of_days_in_month(self, month, year):
        year = int(year)
        day_count = 0
        list_of_dates = [self.service_start_date + timedelta(days=x) for x in
                         range((self.service_end_date - self.service_start_date).days)]
        # above does not include self.service_end_date itself
        list_of_dates.append(self.service_end_date)
        for date in list_of_dates:
            if date.month == month and date.year == year:
                day_count += 1
        return day_count


class CarMiles(models.Model):
    submit_date = models.DateField(auto_now_add=True)
    reading_date = models.DateField()
    odometer_reading = models.IntegerField()

    class Meta:
        verbose_name_plural = "Car Miles"
        ordering = ["reading_date"]

    def get_cname(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.reading_date} ({self.id})"

    @property
    def get_measurement_units(self):
        return "Miles / Month"

    @property
    def get_name(self):
        return self._meta.verbose_name_plural

    @property
    def get_miles_per_month(self):
        try:
            if self.reading_date.month == 12:
                next_months_datapoint = CarMiles.objects.get(reading_date__year=self.reading_date.year + 1,
                                                             reading_date__month=1)
            else:
                next_months_datapoint = CarMiles.objects.get(reading_date__year=self.reading_date.year,
                                                             reading_date__month=self.reading_date.month + 1)
            return next_months_datapoint.odometer_reading - self.odometer_reading
        except CarMiles.DoesNotExist:
            return None