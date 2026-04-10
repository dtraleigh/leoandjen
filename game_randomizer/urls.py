from django.urls import path

from game_randomizer import views

app_name = "game_randomizer"
urlpatterns = [
    path("", views.randomizer, name="randomizer"),
    path("games/", views.game_list, name="game_list"),
    path("api/spin/", views.api_spin, name="api_spin"),
    path("game/<int:game_id>/", views.game_detail, name="game_detail"),
    path("game/<int:game_id>/review/", views.save_review, name="save_review"),
]
