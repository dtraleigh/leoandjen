# Generated by Django 4.1.10 on 2023-08-22 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0015_delete_electricrateschedule"),
    ]

    operations = [
        migrations.CreateModel(
            name="ElectricRateSchedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("submit_date", models.DateField(auto_now_add=True)),
                ("comments", models.TextField(blank=True, null=True)),
                ("schedule_start_date", models.DateField(blank=True, null=True)),
                ("schedule_end_date", models.DateField(blank=True, null=True)),
                ("schedule_end_date_perpetual", models.BooleanField(default=False)),
                (
                    "energy_charge_per_kwh",
                    models.DecimalField(
                        decimal_places=8, max_digits=9, verbose_name="Charge per kWh"
                    ),
                ),
                (
                    "electricity_bills",
                    models.ManyToManyField(blank=True, to="data.electricity"),
                ),
            ],
            options={
                "verbose_name_plural": "Electricity Rate Schedules",
                "ordering": ["name"],
            },
        ),
        migrations.DeleteModel(name="ElectricRateSchedule2",),
    ]
