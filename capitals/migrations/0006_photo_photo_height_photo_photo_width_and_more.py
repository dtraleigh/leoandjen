# Generated by Django 4.1.8 on 2023-06-27 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("capitals", "0005_alter_country_flag_alter_photo_photo_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="photo_height",
            field=models.IntegerField(default=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="photo",
            name="photo_width",
            field=models.IntegerField(default=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="photo",
            name="photo_file",
            field=models.ImageField(
                height_field="photo_height",
                upload_to="photos/",
                width_field="photo_width",
            ),
        ),
    ]