# Generated by Django 4.1.10 on 2024-04-27 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0022_authtoken_alter_electricity_net_metering_credit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authtoken",
            name="access_token",
            field=models.CharField(max_length=1024),
        ),
        migrations.AlterField(
            model_name="authtoken",
            name="refresh_token",
            field=models.CharField(max_length=1024),
        ),
    ]
