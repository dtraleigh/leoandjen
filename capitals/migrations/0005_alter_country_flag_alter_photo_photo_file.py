# Generated by Django 4.1.8 on 2023-06-09 20:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("capitals", "0004_alter_country_flag_alter_photo_photo_file"),
    ]

    operations = [
        migrations.AlterField(
            model_name="country",
            name="flag",
            field=models.ImageField(upload_to="flags/"),
        ),
        migrations.AlterField(
            model_name="photo",
            name="photo_file",
            field=models.ImageField(upload_to="photos/"),
        ),
    ]