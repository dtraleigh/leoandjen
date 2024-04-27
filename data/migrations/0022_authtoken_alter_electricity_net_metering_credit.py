# Generated by Django 4.1.10 on 2024-04-27 15:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0021_alter_electricrateschedule_energy_charge_per_kwh"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthToken",
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
                ("app", models.CharField(max_length=200)),
                ("access_token", models.CharField(max_length=512)),
                ("refresh_token", models.CharField(max_length=512)),
            ],
        ),
        migrations.AlterField(
            model_name="electricity",
            name="net_metering_credit",
            field=models.IntegerField(
                default=0, verbose_name="Carried Forward Balance"
            ),
        ),
    ]
