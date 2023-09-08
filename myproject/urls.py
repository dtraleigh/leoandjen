from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path('__debug__/', include('debug_toolbar.urls')),
    path("admin/", admin.site.urls),
    path("movies/", include("movies.urls")),
    path("capitals/", include("capitals.urls")),
    path("data/", include("data.urls")),
    path("videos/", include("videos.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
