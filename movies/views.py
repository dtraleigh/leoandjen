from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render

from movies.add_movie import add_movie_from_form
from movies.api import *
from movies.forms import AddMovieForm
from movies.functions import *
from movies.models import Movie, Collection


def home(request):
    search = request.GET.get("search")
    sort = request.GET.get("sort")
    movie_list, search, sort, sort_arrow = get_movies(search, sort, None, "sort_title")
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
    uhd_movies, search, sort, sort_arrow = get_movies(None, sort, "4k", "sort_title")
    breadcrumb = "4K Titles (" + str(len(uhd_movies)) + ")"
    sort_label = "Alphabetical"

    return render(request, "movie_grid.html", {"movie_list": uhd_movies,
                                               "breadcrumb": breadcrumb,
                                               "sort": sort,
                                               "sort_arrow": sort_arrow,
                                               "sort_label": sort_label})


def filter_bd(request):
    sort = request.GET.get("sort")
    bd_movies, search, sort, sort_arrow = get_movies(None, sort, "blu_ray", "sort_title")
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
        Q(formats__name="apple_tv") |
        Q(formats__name="g_play")).distinct().order_by("sort_title")
    breadcrumb = "Streaming Titles (" + str(len(streaming_movies)) + ")"
    sort_label = "Alphabetical"

    return render(request, "movie_grid.html", {"movie_list": streaming_movies,
                                               "breadcrumb": breadcrumb,
                                               "sort_label": sort_label})


def filter_plex(request):
    sort = request.GET.get("sort")
    plex_movies, search, sort, sort_arrow = get_movies(None, sort, "plex", "sort_title")
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
    search = request.GET.get("search")
    breadcrumb = f"Movies directed by {director.name}"

    movie_list = Movie.objects.filter(directors__themoviedb_id=tmdb_id).order_by("-primary_release_year")

    return render(request, "person.html", {"movie_list": movie_list,
                                             "search": search,
                                             "breadcrumb": breadcrumb})


def actor(request, themoviedb_actor_id):
    characters_played_by_actor = Character.objects.filter(themoviedb_actor_id=themoviedb_actor_id)
    search = request.GET.get("search")
    actor_name = characters_played_by_actor[0].actor_name
    breadcrumb = f"Movies with {actor_name}"

    movie_list = \
        Movie.objects.filter(characters__themoviedb_actor_id=themoviedb_actor_id).order_by("-primary_release_year")

    return render(request, "person.html", {"movie_list": movie_list,
                                             "search": search,
                                             "breadcrumb": breadcrumb})


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
