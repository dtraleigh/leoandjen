# Generated by Django 4.1.8 on 2023-06-17 19:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0004_electricrateschedule_comments"),
    ]

    operations = [
        migrations.RemoveField(model_name="electricity", name="energy_charge_per_kwh",),
        migrations.RemoveField(
            model_name="electricity", name="storm_recover_cost_per_kwh",
        ),
    ]