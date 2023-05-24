from django.contrib import admin

from movies.models import (APIUser, Character, Collection, Director, Format,
                           Movie)


class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "primary_release_year", "get_formats",
                    "themoviedb_id", "imdb_id", "sort_title", "modified_date")


class FormatAdmin(admin.ModelAdmin):
    list_display = ("name",)


class APIUserAdmin(admin.ModelAdmin):
    list_display = ("name", "api_key")


class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


class DirectorAdmin(admin.ModelAdmin):
    list_display = ("name", "themoviedb_id")


class CharacterAdmin(admin.ModelAdmin):
    list_display = ("character_name", "actor_name", "credit_id", "order")


admin.site.register(Movie, MovieAdmin)
admin.site.register(Format, FormatAdmin)
admin.site.register(APIUser, APIUserAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Director, DirectorAdmin)
admin.site.register(Character, CharacterAdmin)
