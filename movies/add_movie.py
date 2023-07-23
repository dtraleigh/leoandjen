from movies.api import query_tmdb, query_tmdb_by_imdb_id
from movies.functions import update_characters, update_directors
from movies.models import Format, Movie, Collection


def add_movie_from_form(imdb_id, is_tv_movie, letterboxd_slug, formats, sort_title, collections):
    if Movie.objects.filter(imdb_id=imdb_id).exists():
        return None, "Movie already in the database"

    tmdb_json = query_tmdb_by_imdb_id(imdb_id)
    tmdb_info = query_tmdb(imdb_id)

    if is_tv_movie:
        search_results = "tv_results"
        try:
            title = tmdb_json[search_results][0]["name"]
            year = tmdb_json[search_results][0]["first_air_date"].split("-")[0]
            poster = tmdb_json[search_results][0]["poster_path"]
            themoviedb_id = tmdb_json[search_results][0]["id"]
            genres = "[{'id': 10770, 'name': 'TV Movie'}]"
            letterboxd_url_slug = ""
        except IndexError:
            return None, f"No results for {imdb_id}"
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
            return None, f"No results for {imdb_id}"

    new_movie = Movie.objects.create(title=title,
                                     sort_title=sort_title,
                                     primary_release_year=year,
                                     themoviedb_id=themoviedb_id,
                                     imdb_id=imdb_id,
                                     poster_path=poster,
                                     genre_data=genres,
                                     letterboxd_url_slug=letterboxd_url_slug)
    for f in formats:
        new_movie.formats.add(Format.objects.get(name=f))

    for collection_name in collections:
        Collection.objects.get(name=collection_name).movies.add(new_movie)

    update_directors(new_movie)
    update_characters(new_movie)

    return new_movie, f"{title} was added successfully."
