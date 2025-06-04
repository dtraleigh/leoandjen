from datetime import timedelta

from django.db import models

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