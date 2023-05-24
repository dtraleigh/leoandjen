from django.urls import path

from movies import views

app_name = "movies"
urlpatterns = [
    path("", views.home, name="home"),
    path("4k/", views.filter_4k, name="filter_4k"),
    path("BD/", views.filter_bd, name="filter_bd"),
    path("streaming/", views.filter_streaming, name="filter_streaming"),
    path("plex/", views.filter_plex, name="filter_plex"),
    path("genres/", views.genres, name="genres"),
    path("years/", views.years, name="years"),
    path("rand_movie/", views.rand_movie, name="rand_movie"),
    path("movie/<int:tmdb_id>", views.ind_movie, name="ind_movie"),
    path("director/<int:tmdb_id>", views.director, name="director"),
    path("genre/<str:genre_solo>", views.genre_solo, name="genre_solo"),
    path("collection/<int:collection_id>", views.collection, name="collection"),
    path("actor/<int:themoviedb_actor_id>", views.actor, name="actor"),
    path("add-movie/", views.add_movie, name="add_movie"),
]
