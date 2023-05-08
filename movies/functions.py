import requests
import json
from bs4 import BeautifulSoup
import random

from movies.models import Movie, Director, Character
from movies.api import query_tmdb_movie_credits
from django.db.models import Max
from django.db.models import Q


def get_page_content(link):
    try:
        response = requests.get(link, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"Connection problem to {link}")
        print(e)
        response = None

    return response


def get_letterboxd_page_movie_title(s):
    try:
        return s.find("h1", {"class": "headline-1 js-widont prettify"}).get_text()
    except AttributeError:
        print("Couldn't find a movie_title")
        print(s.find("h1", {"class": "headline-1 js-widont prettify"}))
        return None


def get_letterboxd_page_movie_year(s):
    letterboxd_page_movie_year = None
    letterboxd_page_links = s.find_all("a")
    for link in letterboxd_page_links:
        try:
            if "/films/year/" in link["href"]:
                letterboxd_page_movie_year = link.get_text()
        except KeyError:
            pass
    return letterboxd_page_movie_year


def get_letterboxd_page_avg_rating(s):
    rating = None
    CDATA_script = None
    scripts = s.find_all("script")

    for script in scripts:
        if "CDATA" in str(script):
            CDATA_script = str(script)
    try:
        json_str = CDATA_script.split("/*")[1].split("*/")[1]
        movie_json = json.loads(json_str)
        rating = movie_json["aggregateRating"]["ratingValue"]
        return round(rating, 1)
    except TypeError as e:
        print(e)
        return rating
    except AttributeError as e:
        print(e)
        return rating


def get_sort_character(sort_order):
    if sort_order == "desc":
        return "⌄"
    return "⌃"


def get_movies(search, sort, movie_format_filter, order_by):
    """Sort"""
    if sort == "desc":
        sort = "asc"
        order_by = "-" + order_by
        sort_arrow = get_sort_character("desc")
    else:
        sort = "desc"
        sort_arrow = get_sort_character("asc")

    if search:
        if search.lower() == "3d":
            movie_list = Movie.objects.filter(formats__name="3d").order_by(order_by)
        elif search.lower() == "physical":
            movie_list = get_physical_only(Movie.objects.all().order_by(order_by))
        else:
            movie_list = Movie.objects.filter(Q(title__icontains=search) | Q(comments__icontains=search))
    else:
        movie_list = Movie.objects.order_by(order_by)

    if movie_format_filter:
        movie_list = Movie.objects.filter(formats__name=movie_format_filter).order_by(order_by)

    return movie_list, search, sort, sort_arrow


def get_movie_list_sort(sort, order_by):
    if sort == "desc":
        sort = "asc"
        order_by = "-" + order_by
        sort_arrow = get_sort_character("desc")
    else:
        sort = "desc"
        sort_arrow = get_sort_character("asc")

    return sort, sort_arrow, order_by


def get_random_movie():
    max_id = Movie.objects.all().aggregate(max_id=Max("id"))["max_id"]
    while True:
        pk = random.randint(1, max_id)
        random_movie = Movie.objects.filter(pk=pk).first()
        if random_movie:
            return random_movie


def get_directors_by_tmdb_id(tmdb_id):
    # returns a list of crew json objects with job = "Director"
    movie_credits = query_tmdb_movie_credits(tmdb_id)
    try:
        if movie_credits["id"]:
            directors = [x for x in movie_credits["crew"] if x["job"] == "Director"]
    except KeyError:
        directors = ""

    return directors


def get_cast_by_tmdb_id(tmdb_id):
    # returns a list of cast json objects with known_for_department = "Acting"
    movie_credits = query_tmdb_movie_credits(tmdb_id)
    try:
        if movie_credits["id"]:
            actors = [a for a in movie_credits["cast"] if a["known_for_department"] == "Acting"]
    except KeyError:
        actors = ""

    return actors


def nice_director_string(list_of_directors):
    output = ""
    for count, director in enumerate(list_of_directors):
        if len(list_of_directors) == 1:
            output += f"{director}"
        elif count == len(list_of_directors) - 1:
            output += f"and {director}"
        elif len(list_of_directors) == 2:
            output += f"{director} "
        else:
            output += f"{director}, "

    return output


def html_director_code(list_of_directors):
    output = ""
    for count, director in enumerate(list_of_directors):
        director_html = f"<a href='/movies/director/{director.themoviedb_id}'>{director.name}</a>"
        if len(list_of_directors) == 1:
            output += f"{director_html}"
        elif count == len(list_of_directors) - 1:
            output += f"and {director_html}"
        elif len(list_of_directors) == 2:
            output += f"{director_html} "
        else:
            output += f"{director_html}, "

    return output


def update_directors(movie):
    directors = get_directors_by_tmdb_id(movie.themoviedb_id)

    for director in directors:
        # Check that this director doesn't already exist
        director_tmdb_id = director["id"]
        if not Director.objects.filter(themoviedb_id=director_tmdb_id).exists():
            new_director = Director.objects.create(themoviedb_id=director["id"],
                                                   name=director["name"],
                                                   profile_path=director["profile_path"])

            movie.directors.add(new_director)
        else:
            movie.directors.add(Director.objects.get(themoviedb_id=director_tmdb_id))


def update_characters(movie):
    cast_list = get_cast_by_tmdb_id(movie.themoviedb_id)

    # Only interested in the top 10
    for person in cast_list[:12]:
        credit_id = person["credit_id"]
        if not Character.objects.filter(credit_id=credit_id).exists():
            new_character = Character.objects.create(themoviedb_actor_id=person["id"],
                                                     character_name=person["character"],
                                                     profile_path=person["profile_path"],
                                                     actor_name=person["name"],
                                                     credit_id=person["credit_id"],
                                                     order=person["order"])
            movie.characters.add(new_character)


def get_physical_movies(movie_list):
    # Take a list of movies and remove the ones that are streaming only / return only the ones owned on physical media
    physical_copies = []

    for movie in movie_list:
        for movie_format in movie.formats.all():
            if movie_format.is_physical:
                physical_copies.append(movie)
                break
    return physical_copies


def get_streaming_movies(movie_list):
    # Take a list of movies and return only the ones that you can stream
    streaming_movies = []

    for movie in movie_list:
        for movie_format in movie.formats.all():
            if movie_format.is_streaming:
                streaming_movies.append(movie)
                break
    return streaming_movies
