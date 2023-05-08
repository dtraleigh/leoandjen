# Generated by Django 4.1.8 on 2023-05-07 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="APIUser",
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
                ("name", models.CharField(max_length=50, unique=True)),
                ("api_key", models.CharField(max_length=200, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Character",
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
                ("themoviedb_actor_id", models.IntegerField()),
                ("character_name", models.CharField(max_length=300)),
                (
                    "profile_path",
                    models.CharField(
                        blank=True, default=None, max_length=300, null=True
                    ),
                ),
                ("actor_name", models.CharField(max_length=300)),
                ("credit_id", models.CharField(max_length=300)),
                ("order", models.IntegerField()),
            ],
            options={"ordering": ["order"],},
        ),
        migrations.CreateModel(
            name="Director",
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
                ("themoviedb_id", models.IntegerField()),
                ("name", models.CharField(max_length=300)),
                (
                    "profile_path",
                    models.CharField(
                        blank=True, default=None, max_length=300, null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Format",
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
                ("name", models.CharField(max_length=50, unique=True)),
                ("is_physical", models.BooleanField(default=False)),
                ("is_streaming", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Movie",
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
                ("title", models.CharField(max_length=300)),
                (
                    "sort_title",
                    models.CharField(
                        default=models.CharField(max_length=300), max_length=300
                    ),
                ),
                ("primary_release_year", models.IntegerField()),
                ("themoviedb_id", models.IntegerField()),
                ("imdb_id", models.CharField(max_length=50)),
                ("poster_path", models.CharField(max_length=300)),
                ("comments", models.CharField(blank=True, max_length=300, null=True)),
                ("genre_data", models.JSONField(blank=True, null=True)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("modified_date", models.DateTimeField(auto_now=True)),
                (
                    "letterboxd_url_slug",
                    models.CharField(blank=True, max_length=300, null=True),
                ),
                (
                    "characters",
                    models.ManyToManyField(
                        blank=True, default=None, to="movies.character"
                    ),
                ),
                (
                    "directors",
                    models.ManyToManyField(
                        blank=True, default=None, to="movies.director"
                    ),
                ),
                (
                    "formats",
                    models.ManyToManyField(
                        blank=True, default=None, to="movies.format"
                    ),
                ),
            ],
            options={"ordering": ["sort_title"],},
        ),
        migrations.CreateModel(
            name="Collection",
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
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True, default=None)),
                (
                    "movies",
                    models.ManyToManyField(blank=True, default=None, to="movies.movie"),
                ),
            ],
        ),
    ]
