# Generated by Django 4.1.10 on 2023-08-22 18:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0017_rename_electricrateschedule_electricrateschedule2"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ElectricRateSchedule2", new_name="ElectricRateSchedule",
        ),
    ]
