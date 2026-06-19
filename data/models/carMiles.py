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

    @classmethod
    def get_miles_per_month_map(cls):
        """Return {pk: miles_to_next_calendar_month} for every reading in ONE query.

        Mirrors ``get_miles_per_month`` exactly (None when the next calendar month's
        reading is missing), but lets callers avoid a per-row query.
        """
        readings = list(cls.objects.values("pk", "reading_date", "odometer_reading"))
        odometer_by_month = {
            (r["reading_date"].year, r["reading_date"].month): r["odometer_reading"]
            for r in readings
        }
        result = {}
        for r in readings:
            year = r["reading_date"].year
            month = r["reading_date"].month
            next_key = (year + 1, 1) if month == 12 else (year, month + 1)
            next_odometer = odometer_by_month.get(next_key)
            result[r["pk"]] = (
                next_odometer - r["odometer_reading"] if next_odometer is not None else None
            )
        return result