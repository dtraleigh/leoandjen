from django.urls import path

from data import views

app_name = "data"
urlpatterns = [
    path("", views.home, name="home"),
    path("water/", views.water, name="water"),
    path("gas/", views.gas, name="gas"),
    path("electricity/", views.electricity, name="electricity"),
    path("car_miles/", views.car_miles, name="car_miles"),
    path("upload/", views.upload_files, name="upload_files"),
    path('preview/', views.preview_pdf, name='preview_pdf'),
    # path("export_csv/", views.export_csv, name="export_csv"),
]
