# Generated by Django 4.1.10 on 2023-08-22 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0008_electricrateschedule2"),
    ]

    operations = [
        migrations.AddField(
            model_name="electricrateschedule2",
            name="electricity_bills",
            field=models.ManyToManyField(blank=True, null=True, to="data.electricity"),
        ),
        migrations.AddField(
            model_name="electricrateschedule2",
            name="schedule_end_date_perpetual",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="electricrateschedule2",
            name="schedule_end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="electricrateschedule2",
            name="schedule_start_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
