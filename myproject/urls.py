from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('__debug__/', include('debug_toolbar.urls')),
    path("admin/", admin.site.urls),
    path("movies/", include("movies.urls")),
    path("capitals/", include("capitals.urls")),
    path("data/", include("data.urls")),
    path("videos/", include("videos.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
