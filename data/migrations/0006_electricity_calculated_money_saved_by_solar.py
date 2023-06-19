# Generated by Django 4.1.8 on 2023-06-19 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0005_remove_electricity_energy_charge_per_kwh_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="electricity",
            name="calculated_money_saved_by_solar",
            field=models.DecimalField(
                blank=True,
                decimal_places=8,
                max_digits=9,
                null=True,
                verbose_name="Energy Charge per kWh",
            ),
        ),
    ]
