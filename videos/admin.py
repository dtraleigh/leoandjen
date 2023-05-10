from django.contrib import admin
from videos.models import *


class VideoAdmin(admin.ModelAdmin):
    list_display = ("name", "date_added", "date_shot", "poster", "video_file", "get_tags", "lat", "lon")


class ExternalAdmin(admin.ModelAdmin):
    list_display = ("name", "date_added", "date_shot", "get_tags", "lat", "lon")


class AlbumAdmin(admin.ModelAdmin):
    list_display = ("name", "date_added", "poster", "description")


class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "date_added")


class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "label", "lat", "lon", "html_id")


admin.site.register(Video, VideoAdmin)
admin.site.register(ExternalVideo, ExternalAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Location, LocationAdmin)
