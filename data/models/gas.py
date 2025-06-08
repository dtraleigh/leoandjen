from datetime import timedelta

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class Gas(models.Model):
    submit_date = models.DateField(auto_now_add=True)
    bill_date = models.DateField(blank=True, null=True)
    service_start_date = models.DateField()
    service_end_date = models.DateField()
    therms_usage = models.IntegerField()
    uploaded_pdf = models.FileField(
        upload_to="gas_pdfs/",
        blank=True,
        null=True,
        verbose_name="Uploaded PDF Bill"
    )

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

@receiver(post_delete, sender=Gas)
def delete_uploaded_pdf_from_s3(sender, instance, **kwargs):
    if instance.uploaded_pdf:
        instance.uploaded_pdf.delete(save=False)