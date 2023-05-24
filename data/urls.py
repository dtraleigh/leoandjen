from django.urls import path

from data import views

app_name = "data"
urlpatterns = [
    path("", views.home, name="home"),
    path("water/", views.water, name="water"),
    path("gas/", views.gas, name="gas"),
    path("electricity/", views.electricity, name="electricity"),
    path("car_miles/", views.car_miles, name="car_miles"),
    # path("export_csv/", views.export_csv, name="export_csv"),
]
