# Generated by Django 4.1.10 on 2023-08-22 17:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0012_electricrateschedule2_elec_bills_schedule"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="electricrateschedule2", name="elec_bills_schedule",
        ),
    ]
