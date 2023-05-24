from django.urls import path

from videos import views

app_name = "videos"
urlpatterns = [
    path(r"", views.video_login),
    path("main/", views.main),
    path("map/", views.map_view),
    path("main/upload/", views.upload),
    path("random/", views.random_shot_view),
    path("logout/", views.video_logout),
    path("album/<int:album_id>", views.album_view, name="album_view"),
    path("album/<int:album_id>/<str:shot_type>/<int:shot_id>", views.shot_view),
    path("tag/<str:tag_name>/<str:shot_type>/<int:shot_id>", views.video_tag_view),
    path("tag/<str:tag_name>", views.tag_view),
    path("recent/<str:shot_type>/<int:shot_id>", views.recent_view, name="recent_shot"),
    path("edit/<str:shot_type>/<int:shot_id>", views.shot_edit_view),
    path("map/<str:shot_type>/<int:shot_id>", views.map_shot),
]
