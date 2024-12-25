from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse

from movies.add_movie import add_movie_from_form
from movies.api import *
from movies.forms import AddMovieForm, EditMovieForm
from movies.functions import *
from movies.models import Movie, Collection, Format


def home(request):
    search = request.GET.get("search")
    sort = request.GET.get("sort")
    movie_list, search, sort, sort_arrow = get_movies(search, sort, None, None)
    breadcrumb = str(len(movie_list)) + " Titles"
    sort_label = "Alphabetical"
    movie_recent_list = Movie.objects.order_by("-created_date")[0:12]
    collections = Collection.objects.all()

    if search:
        director_list = Director.objects.filter(name__icontains=search)
    else:
        director_list = []

    return render(request, "home.html", {"movie_list": movie_list,
                                         "search": search,
                                         "breadcrumb": breadcrumb,
                                         "sort": sort,
                                         "sort_arrow": sort_arrow,
                                         "sort_label": sort_label,
                                         "movie_recent_list": movie_recent_list,
                                         "director_list": director_list,
                                         "collections": collections})


def filter_4k(request):
    sort = request.GET.get("sort")
    uhd_movies, search, sort, sort_arrow = get_movies(None, sort, "4k", None)
    breadcrumb = "4K Titles (" + str(len(uhd_movies)) + ")"
    sort_label = "Alphabetical"

    return render(request, "movie_grid.html", {"movie_list": uhd_movies,
                                               "breadcrumb": breadcrumb,
                                               "sort": sort,
                                               "sort_arrow": sort_arrow,
                                               "sort_label": sort_label})


def filter_bd(request):
    sort = request.GET.get("sort")
    bd_movies, search, sort, sort_arrow = get_movies(None, sort, "blu_ray", None)
    breadcrumb = "Blu-Ray Titles (" + str(len(bd_movies)) + ")"
    sort_label = "Alphabetical"

    return render(request, "movie_grid.html", {"movie_list": bd_movies,
                                               "breadcrumb": breadcrumb,
                                               "sort": sort,
                                               "sort_arrow": sort_arrow,
                                               "sort_label": sort_label})


def filter_streaming(request):
    streaming_movies = Movie.objects.filter(
        Q(formats__name="amz") |
        Q(formats__name="vudu") |
        Q(formats__name="ma") |
        Q(formats__name="g_play")).distinct().order_by("sort_title")
    breadcrumb = "Streaming Titles (" + str(len(streaming_movies)) + ")"
    sort_label = "Alphabetical"

    return render(request, "movie_grid.html", {"movie_list": streaming_movies,
                                               "breadcrumb": breadcrumb,
                                               "sort_label": sort_label})


def filter_plex(request):
    sort = request.GET.get("sort")
    plex_movies, search, sort, sort_arrow = get_movies(None, sort, "plex", None)
    breadcrumb = "Titles on Plex (" + str(len(plex_movies)) + ")"
    sort_label = "Alphabetical"

    return render(request, "movie_grid.html", {"movie_list": plex_movies,
                                               "breadcrumb": breadcrumb,
                                               "sort": sort,
                                               "sort_arrow": sort_arrow,
                                               "sort_label": sort_label})


def genres(request):
    movie_list = Movie.objects.all().order_by("sort_title")
    breadcrumb = "Titles sorted by Genre"
    sort_label = "Alphabetical"

    physical_only_flag = request.GET.get("physical")
    if physical_only_flag == "true":
        movie_list = get_physical_movies(movie_list)

    streaming_only_flag = request.GET.get("streaming")
    if streaming_only_flag == "true":
        movie_list = get_streaming_movies(movie_list)

    # ["Action", "Romance", ...]
    all_genres = []
    for movie in movie_list:
        for genre in movie.genre_data:
            all_genres.append(genre["name"])
    all_genres = list(set(all_genres))
    all_genres.sort()

    # [["Genre 1", Movie A], ["Genre 2", Movie A] ...]
    movie_list_w_genres = []
    for movie in movie_list:
        for genre in movie.genre_data:
            movie_list_w_genres.append([genre["name"], movie])

    return render(request, "genres.html", {"movie_list": movie_list_w_genres,
                                           "all_genres": all_genres,
                                           "breadcrumb": breadcrumb,
                                           "sort_label": sort_label})


def years(request):
    sort = request.GET.get("sort")
    breadcrumb = "Titles sorted by Year"
    sort_label = "Release Year"
    movie_list, search, sort, sort_arrow = get_movies(None, sort, None, "primary_release_year")

    physical_only_flag = request.GET.get("physical")
    if physical_only_flag == "true":
        movie_list = get_physical_movies(movie_list)

    streaming_only_flag = request.GET.get("streaming")
    if streaming_only_flag == "true":
        movie_list = get_streaming_movies(movie_list)

    return render(request, "movie_grid.html", {"movie_list": movie_list,
                                               "breadcrumb": breadcrumb,
                                               "sort": sort,
                                               "sort_arrow": sort_arrow,
                                               "sort_label": sort_label})


def rand_movie(request):
    return redirect(f"/movies/movie/{get_random_movie().themoviedb_id}")


def ind_movie(request, tmdb_id):
    movie_info = query_tmdb(tmdb_id)
    movie = Movie.objects.get(themoviedb_id=tmdb_id)

    if movie.letterboxd_url_slug:
        letterboxd_page = get_page_content(f"https://letterboxd.com/film/{movie.letterboxd_url_slug}")
        letterboxd_page_soup = BeautifulSoup(letterboxd_page.content, "html.parser")
        letterboxd_page_avg_rating = get_letterboxd_page_avg_rating(letterboxd_page_soup)
    else:
        letterboxd_page_avg_rating = None

    try:
        if movie_info["id"]:
            title = movie_info["title"]
            year = movie_info["release_date"][:4]
            tagline = movie_info["tagline"]
            poster_path = movie_info["poster_path"]
            overview = movie_info["overview"]
            runtime = str(movie_info["runtime"])
            genres_list = [g["name"] for g in movie_info["genres"]]
    except KeyError:
        title = movie.title
        year = movie.primary_release_year
        tagline = None
        poster_path = movie.poster_path
        overview = None
        runtime = None
        genres_list = genres

    list_of_directors = [x for x in movie.directors.all()]
    directors_string = html_director_code(list_of_directors)

    character_list = movie.characters.all()

    return render(request, "movie.html", {"tmdb_id": tmdb_id,
                                          "title": title,
                                          "year": year,
                                          "tagline": tagline,
                                          "poster_path": poster_path,
                                          "overview": overview,
                                          "runtime": runtime,
                                          "movie": movie,
                                          "genres_list": genres_list,
                                          "rating": letterboxd_page_avg_rating,
                                          "directors": directors_string,
                                          "character_list": character_list})


def director(request, tmdb_id):
    director = Director.objects.get(themoviedb_id=tmdb_id)
    director_info = get_person_info_from_tmdb(tmdb_id)

    try:
        if director_info["id"]:
            director_birthday = director_info["birthday"]
            director_deathday = director_info["deathday"]
            director_biography = director_info["biography"]
    except KeyError:
        director_birthday = None
        director_deathday = None
        director_biography = None

    movie_list_at_home = Movie.objects.filter(directors__themoviedb_id=tmdb_id).order_by("-primary_release_year")

    director_credits_as_crew = get_actors_movies_from_tmdb(tmdb_id)["crew"]
    movies_they_directed = [m for m in director_credits_as_crew if m["job"] == "Director"]
    movies_not_at_home = [f for f in movies_they_directed if
                          f["id"] not in [m.themoviedb_id for m in movie_list_at_home]]
    sorted_movies_not_at_home = sorted(movies_not_at_home, key=lambda x: x['popularity'], reverse=True)

    return render(request, "person.html", {"person_poster_path": director.profile_path,
                                           "person_name": director_info["name"],
                                           "birthday": director_birthday,
                                           "deathday": director_deathday,
                                           "biography": director_biography,
                                           "movie_list_at_home": movie_list_at_home,
                                           "movie_list_other": sorted_movies_not_at_home})


def actor(request, themoviedb_actor_id):
    actor_info_from_character = Character.objects.filter(themoviedb_actor_id=themoviedb_actor_id)[0]
    actor_info = get_person_info_from_tmdb(themoviedb_actor_id)

    try:
        if actor_info["id"]:
            actor_birthday = actor_info["birthday"]
            actor_deathday = actor_info["deathday"]
            actor_biography = actor_info["biography"]
    except KeyError:
            actor_birthday = None
            actor_deathday = None
            actor_biography = None

    movie_list_at_home = \
        Movie.objects.filter(characters__themoviedb_actor_id=themoviedb_actor_id).order_by("-primary_release_year")

    actor_credits_as_cast = get_actors_movies_from_tmdb(themoviedb_actor_id)["cast"]
    movies_not_at_home = [f for f in actor_credits_as_cast if f["id"] not in [m.themoviedb_id for m in movie_list_at_home]]
    sorted_movies_not_at_home = sorted(movies_not_at_home, key=lambda x: x['popularity'], reverse=True)

    return render(request, "person.html", {"person_poster_path": actor_info_from_character.profile_path,
                                            "person_name": actor_info_from_character.actor_name,
                                            "birthday": actor_birthday,
                                            "deathday": actor_deathday,
                                            "biography": actor_biography,
                                            "movie_list_at_home": movie_list_at_home,
                                           "movie_list_other": sorted_movies_not_at_home})


def genre_solo(request, genre_solo):
    search = request.GET.get("search")
    breadcrumb = f"Genre - {genre_solo}"

    movie_list = []

    for movie in Movie.objects.all():
        movies_genres = movie.genre_data
        for movies_genre in movies_genres:
            if movies_genre["name"] == genre_solo:
                movie_list.append(movie)
                break

    return render(request, "genre_ind.html", {"movie_list": movie_list,
                                              "search": search,
                                              "breadcrumb": breadcrumb})


def collection(request, collection_id):
    sort = request.GET.get("sort")
    sort, sort_arrow, order_by = get_movie_list_sort(sort, "sort_title")

    this_collection = Collection.objects.get(id=collection_id)
    movies = [movie for movie in this_collection.movies.all().order_by(order_by)]

    breadcrumb = f"{this_collection.name} collection ({str(len(movies))})"
    sort_label = "Alphabetical"

    return render(request, "movie_grid.html", {"movie_list": movies,
                                               "breadcrumb": breadcrumb,
                                               "sort": sort,
                                               "sort_arrow": sort_arrow,
                                               "sort_label": sort_label})


@login_required(login_url="/admin")
def add_movie(request):
    output_message = None
    if request.method == "POST":
        form = AddMovieForm(request.POST)

        if form.is_valid():
            imdb_id = form.cleaned_data["imdb_id"]
            is_tv_movie = form.cleaned_data["is_tv_movie"]
            letterboxd_slug = form.cleaned_data["letterboxd_slug"]
            formats = form.cleaned_data["formats"]
            sort_title = form.cleaned_data["sort_title"]
            collections = form.cleaned_data["collections"]

            new_movie, output_message = add_movie_from_form(
                                                                imdb_id,
                                                                is_tv_movie,
                                                                letterboxd_slug,
                                                                formats,
                                                                sort_title,
                                                                collections
                                                            )
            messages.info(request, output_message)

            return HttpResponseRedirect("/movies/add-movie/")
    else:
        form = AddMovieForm()

    return render(request, "add_movie.html", {"form": form,
                                              "message": output_message})


@login_required(login_url="/admin")
def edit_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":
        form = EditMovieForm(request.POST, instance=movie)
        if form.is_valid():
            imdb_id = form.cleaned_data["imdb_id"]
            letterboxd_slug = form.cleaned_data["letterboxd_slug"]
            formats = form.cleaned_data["formats"]
            sort_title = form.cleaned_data["sort_title"]
            collections = form.cleaned_data["collections"]

            movie.imdb_id = imdb_id
            movie.letterboxd_url_slug = letterboxd_slug
            movie.sort_title = sort_title if sort_title else movie.title
            movie.save()

            movie.formats.clear()
            for format_name in formats:
                movie.formats.add(Format.objects.get(name=format_name))

            movie.collection_set.clear()
            for collection_name in collections:
                Collection.objects.get(name=collection_name).movies.add(movie)

            messages.info(request, f"{movie.title} was updated successfully.")
            return HttpResponseRedirect(f"/movies/movie/{movie.themoviedb_id}/")
    else:
        form = EditMovieForm(instance=movie)

    return render(request, "edit_movie.html", {"form": form, "movie": movie})
