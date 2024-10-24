from django.db import models
from django.db.models import Case, When
from django.db.models.functions import Coalesce


class Movie(models.Model):
    title = models.CharField(max_length=300)
    sort_title = models.CharField(max_length=300, blank=True, null=True, default=title)
    primary_release_year = models.IntegerField()
    themoviedb_id = models.IntegerField()
    imdb_id = models.CharField(max_length=50)
    poster_path = models.CharField(max_length=300)
    formats = models.ManyToManyField("Format", default=None, blank=True)
    comments = models.CharField(max_length=300, blank=True, null=True)
    genre_data = models.JSONField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    letterboxd_url_slug = models.CharField(max_length=300, blank=True, null=True)
    directors = models.ManyToManyField("Director", default=None, blank=True)
    characters = models.ManyToManyField("Character", default=None, blank=True)

    class Meta:
        ordering = [
            Coalesce(
                Case(
                    When(sort_title="", then=None),
                    default="sort_title",
                    output_field=models.CharField(),
                ),
                "title",
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.primary_release_year})"

    def get_formats(self):
        return ", ".join([f.name for f in self.formats.all()])

    @property
    def get_sort_title(self):
        return self.sort_title or self.title


class Format(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_physical = models.BooleanField(default=False)
    is_streaming = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class APIUser(models.Model):
    name = models.CharField(max_length=50, unique=True)
    api_key = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Collection(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default=None, blank=True)
    movies = models.ManyToManyField("Movie", default=None, blank=True)

    def __str__(self):
        return self.name


class Director(models.Model):
    themoviedb_id = models.IntegerField()
    name = models.CharField(max_length=300)
    profile_path = models.CharField(max_length=300, default=None, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.themoviedb_id})"

    @property
    def get_number_of_movies_directed(self):
        number_of_movies_directed = 0
        for movie in Movie.objects.all():
            if self in movie.directors.all():
                number_of_movies_directed += 1

        return number_of_movies_directed


class Character(models.Model):
    themoviedb_actor_id = models.IntegerField()
    character_name = models.CharField(max_length=300)
    profile_path = models.CharField(max_length=300, default=None, blank=True, null=True)
    actor_name = models.CharField(max_length=300)
    credit_id = models.CharField(max_length=300)
    order = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.character_name} played by {self.actor_name} ({self.credit_id})"
