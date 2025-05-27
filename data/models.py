import decimal
import logging
from datetime import timedelta
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Q, Max
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger("django")


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

    @classmethod
    def get_last_production_date(cls):
        """Returns the date of the most recent SolarEnergy instance in YYYY-MM-DD format."""
        last_date = cls.objects.aggregate(Max('date_of_production'))['date_of_production__max']
        return last_date.strftime('%Y-%m-%d') if last_date else None


class Electricity(models.Model):
    submit_date = models.DateField(auto_now_add=True)
    bill_date = models.DateField(blank=True, null=True)
    service_start_date = models.DateField()
    service_end_date = models.DateField()
    kWh_usage = models.IntegerField("Energy Used (Grid Energy Consumed)")
    solar_amt_sent_to_grid = models.IntegerField("Energy Delivered to Grid (Solar Sent to Grid)")
    net_metering_credit = models.IntegerField("Carried Forward Balance", default=0)
    calculated_money_saved_by_solar = models.DecimalField(max_digits=9,
                                                          decimal_places=2,
                                                          blank=True, null=True,
                                                          verbose_name="Calc $$ Saved")
    uploaded_pdf = models.FileField(
        upload_to="electricity_pdfs/",
        blank=True,
        null=True,
        verbose_name="Uploaded PDF Bill"
    )

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

    # Not all bill's have a bill_date so we use service_start_date
    @property
    def get_previous_month_bill(self):
        """Return the bill whose service_start_date is exactly one calendar
                month before this bill, or None if it doesn’t exist."""
        this_bills_year_start = self.service_start_date.year
        this_bills_month_start = self.service_start_date.month

        # Compute previous month
        if this_bills_month_start == 1:
            prev_bills_month_start = 12
            prev_bills_year_start = this_bills_year_start - 1
        else:
            prev_bills_month_start = this_bills_month_start - 1
            prev_bills_year_start = this_bills_year_start

        return Electricity.objects.filter(service_start_date__year=prev_bills_year_start,
                                       service_start_date__month=prev_bills_month_start).first()

    @property
    def get_money_saved_by_solar(self):
        from data.functions import get_days_energy_charge_per_kwh, get_days_storm_recover_cost_per_kwh
        # Returns as a Decimal rounded to 2 DP
        decimal.getcontext().rounding = decimal.ROUND_HALF_UP

        prev_bill = self.get_previous_month_bill
        if not prev_bill:
            logger.warning(f"No previous bill found for bill ID {self.id}. calculated_money_saved_by_solar defaults to 0.00.")
            return Decimal("0.00")
        else:
            credited_solar = prev_bill.net_metering_credit + self.solar_amt_sent_to_grid
        billed_kwh = self.kWh_usage - credited_solar
        if billed_kwh < 0:
            this_bills_kwh_saved = self.kWh_usage
        else:
            this_bills_kwh_saved = credited_solar

        this_bills_kwh_saved_per_day = this_bills_kwh_saved / self.get_number_of_days.days

        try:
            savings = Decimal("0.00")

            increment_date = self.service_start_date
            while increment_date != self.service_end_date + timedelta(days=1):
                savings += Decimal(this_bills_kwh_saved_per_day) * \
                           get_days_energy_charge_per_kwh(increment_date.month, increment_date.day, increment_date.year)
                savings += Decimal(this_bills_kwh_saved_per_day) * get_days_storm_recover_cost_per_kwh(
                    increment_date.month, increment_date.day,
                    increment_date.year)
                increment_date += timedelta(days=1)

            return savings.quantize(Decimal("1.00"))
        except TypeError as e:
            logger.exception(e)
            return Decimal("0.00")

    @property
    def bill_is_lacking_rates(self):
        bill_is_lacking_rates = False
        increment_date = self.service_start_date
        while increment_date != self.service_end_date + timedelta(days=1):
            try:
                energy_rate_schedule = ElectricRateSchedule.objects.get(electricity_bills=self)
                storm_rec_schedule = ElectricRateSchedule.objects.get(Q(schedule_start_date__lte=increment_date,
                                                                        schedule_end_date__gte=increment_date,
                                                                        name__iexact="Storm Recovery Costs") |
                                                                      Q(schedule_start_date__lte=increment_date,
                                                                        schedule_end_date_perpetual=True,
                                                                        name__iexact="Storm Recovery Costs"))
                increment_date += timedelta(days=1)
            except Exception as e:
                bill_is_lacking_rates = True
                break

        return bill_is_lacking_rates

    def calculate_and_set_money_saved(self):
        try:
            self.calculated_money_saved_by_solar = self.get_money_saved_by_solar
        except Exception as e:
            logger.exception(e)
            self.calculated_money_saved_by_solar = Decimal("0.00")


class ElectricRateSchedule(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    submit_date = models.DateField(auto_now_add=True)
    comments = models.TextField(blank=True, null=True)
    schedule_start_date = models.DateField(blank=True, null=True)
    schedule_end_date = models.DateField(blank=True, null=True)
    schedule_end_date_perpetual = models.BooleanField(default=False)
    energy_charge_per_kwh = models.DecimalField(max_digits=9,
                                                decimal_places=8,
                                                verbose_name="Charge per kWh", blank=True, null=True)
    electricity_bills = models.ManyToManyField("Electricity", blank=True)

    class Meta:
        verbose_name_plural = "Electricity Rate Schedules"
        ordering = ["name"]

    def __str__(self):
        if self.schedule_end_date_perpetual:
            return f"{self.name}, id: {self.id} ({self.schedule_start_date.month}-{self.schedule_start_date.year} " \
                   f"until....)"
        return f"{self.name}, id: {self.id} ({self.schedule_start_date.month}-{self.schedule_start_date.year} to " \
               f"{self.schedule_end_date.month}-{self.schedule_end_date.year})"


@receiver(post_save, sender=Electricity)
def update_money_saved_by_solar_on_instance(sender, created, instance, **kwargs):
    from data.functions import associate_elec_bills_to_rates
    associate_elec_bills_to_rates()

    try:
        value = instance.get_money_saved_by_solar
    except Exception as e:
        logger.exception(e)
        value = Decimal("0.00")

    Electricity.objects.filter(pk=instance.pk).update(
        calculated_money_saved_by_solar=value
    )

    # Update other stale bills from 2023+ that have 0.00 saved solar value
    stale_bills = Electricity.objects.filter(
        service_start_date__year__gte=2023,
        calculated_money_saved_by_solar=Decimal("0.00")
    )

    for bill in stale_bills:
        try:
            value = bill.get_money_saved_by_solar
        except Exception as e:
            logger.exception(e)
            value = Decimal("0.00")
        Electricity.objects.filter(pk=bill.pk).update(
            calculated_money_saved_by_solar=value
        )


@receiver(post_save, sender=ElectricRateSchedule)
def update_money_saved_by_solar_on_instances(sender, created, instance, **kwargs):
    from data.functions import associate_elec_bills_to_rates
    associate_elec_bills_to_rates()

    bills = Electricity.objects.filter(service_end_date__year__gte=2023)

    updated_bills = []
    for bill in bills:
        try:
            bill.calculated_money_saved_by_solar = bill.get_money_saved_by_solar
            updated_bills.append(bill)
        except Exception as e:
            logger.exception(f"Failed to calculate savings for bill ID {bill.id}: {e}")

    with transaction.atomic():
        Electricity.objects.bulk_update(updated_bills, ['calculated_money_saved_by_solar'])


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


class AuthToken(models.Model):
    name = models.CharField(max_length=200)
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200)
    app_code = models.CharField(max_length=200)
    redirect_uri = models.CharField(max_length=200)
    access_token = models.CharField(max_length=1024)
    refresh_token = models.CharField(max_length=1024)
    issued_datetime = models.DateTimeField(auto_now=True)
    expires_in = models.IntegerField(default=1000)

    def __str__(self):
        return f"{self.id}"

    def is_token_expired(self, buffer=0):
        """
        Checks if the token is expired or will expire within the given buffer time.
        Returns True if expired or about to expire (considering the buffer), False otherwise.
        """
        expiration_time = self.issued_datetime + timedelta(seconds=self.expires_in)
        expiration_with_buffer = expiration_time - timedelta(seconds=buffer)
        return expiration_with_buffer <= timezone.now()
