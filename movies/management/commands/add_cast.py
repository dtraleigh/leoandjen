from django.core.management.base import BaseCommand

from movies.models import *
from movies.api import *
from movies.functions import update_characters, update_directors


class Command(BaseCommand):
    def handle(self, *args, **options):
        all_movies = Movie.objects.all()
        # all_movies = [Movie.objects.get(title="Top Gun: Maverick")]

        for movie in all_movies:
            print(f"Updating {movie.title}")
            update_directors(movie)
            update_characters(movie)

