# Generated by Django 4.1.8 on 2023-05-24 16:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "capitals",
            "0002_remove_photo_photo_height_remove_photo_photo_width_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(model_name="photo", name="is_capitol",),
    ]