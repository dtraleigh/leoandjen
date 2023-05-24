from django.urls import path

from capitals import views

app_name = "capitals"
urlpatterns = [
    path("", views.home, name="home"),
    path("map/", views.map_page, name="map_page"),
    path("capital/<str:cap_name>", views.capital_page, name="capital_page"),
]
