# Generated by Django 5.1.2 on 2024-12-19 19:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='authtoken',
            old_name='app',
            new_name='name',
        ),
    ]
