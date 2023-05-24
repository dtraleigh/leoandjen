from django.core.management.base import BaseCommand

from movies.functions import update_characters, update_directors
from movies.models import Movie


class Command(BaseCommand):
    def handle(self, *args, **options):
        all_movies = Movie.objects.all()

        for movie in all_movies:
            print(f"Updating {movie.title}")
            update_directors(movie)
            update_characters(movie)
