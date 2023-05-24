import sys

from django.core.management.base import BaseCommand

from movies.api import query_tmdb, query_tmdb_by_imdb_id
from movies.functions import (nice_director_string, update_characters,
                              update_directors)
from movies.models import Format, Movie

# keeping around but adding movies using the UI is now the preferred method.


class Command(BaseCommand):
    help = "Example: add_movie tt0443543 -l the-illusionist -f plex"

    def add_arguments(self, parser):
        # Required arguments
        parser.add_argument("imdb_id", help="IMDB ID of movie to add")

        # Optional arguments
        parser.add_argument("-f", "--format", metavar="\b",
                            help="Add a list of formats. All options: vudu, plex, ma, hddvd, g_play, dvd, blu_ray, 4k, 3d, amz, apple_tv", )
        parser.add_argument("-t", "--tv_movie", action="store_true", help="Indicates that movie is from tv_results")
        parser.add_argument("-l", "--letterboxd_slug", metavar="\b",
                            help="Populate the url slug from the letterboxd website")

    def handle(self, *args, **options):
        imdb_id = options["imdb_id"]
        letterboxd_slug = options["letterboxd_slug"]
        formats = options["format"]  # ["vudu", "plex", "ma", "hddvd", "g_play", "dvd", "blu_ray", "4k", "3d", "amz"]
        formats_split = formats.split(",")
        tv_movie = options["tv_movie"]

        tmdb_json = query_tmdb_by_imdb_id(imdb_id)
        tmdb_info = query_tmdb(imdb_id)

        if tv_movie:
            search_results = "tv_results"
            try:
                title = tmdb_json[search_results][0]["name"]
                year = tmdb_json[search_results][0]["first_air_date"].split("-")[0]
                poster = tmdb_json[search_results][0]["poster_path"]
                themoviedb_id = tmdb_json[search_results][0]["id"]
                genres = "[{'id': 10770, 'name': 'TV Movie'}]"
                letterboxd_url_slug = ""
            except IndexError:
                print("No results for " + imdb_id)
                sys.exit(1)
        else:
            search_results = "movie_results"
            try:
                title = tmdb_json[search_results][0]["title"]
                year = tmdb_json[search_results][0]["release_date"].split("-")[0]
                poster = tmdb_json[search_results][0]["poster_path"]
                themoviedb_id = tmdb_json[search_results][0]["id"]
                genres = tmdb_info["genres"]
                letterboxd_url_slug = letterboxd_slug
            except IndexError:
                print(f"No results for {imdb_id}")
                sys.exit(1)

        new_movie = Movie.objects.create(title=title,
                                         sort_title=title,
                                         primary_release_year=year,
                                         themoviedb_id=themoviedb_id,
                                         imdb_id=imdb_id,
                                         poster_path=poster,
                                         genre_data=genres,
                                         letterboxd_url_slug=letterboxd_url_slug)
        for f in formats_split:
            new_movie.formats.add(Format.objects.get(name=f))

        update_directors(new_movie)
        update_characters(new_movie)

        list_of_directors = [x.name for x in new_movie.directors.all()]
        directors_string = nice_director_string(list_of_directors)
        print(f"Movie '{title}' ({str(year)}) added. Directed by {directors_string}")
