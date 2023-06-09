# Generated by Django 4.1.8 on 2023-06-16 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0001_initial"),
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
                ("submit_date", models.DateField(auto_now_add=True)),
                ("schedule_start_date", models.DateField()),
                ("schedule_end_date", models.DateField()),
                (
                    "energy_charge_per_kwh",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=9,
                        null=True,
                        verbose_name="Energy Charge per kWh",
                    ),
                ),
                (
                    "storm_recover_cost_per_kwh",
                    models.DecimalField(
                        blank=True,
                        decimal_places=8,
                        max_digits=9,
                        null=True,
                        verbose_name="Storm Recovery Cost per kWh",
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Electricity Rate Schedules",
                "ordering": ["schedule_start_date"],
            },
        ),
        migrations.RemoveField(model_name="electricity", name="energy_charge_per_kwh",),
        migrations.RemoveField(
            model_name="electricity", name="storm_recover_cost_per_kwh",
        ),
    ]
