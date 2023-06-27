from django.contrib import admin

from capitals.models import Capital, Country, Photo


class PhotoAdmin(admin.ModelAdmin):
    list_display = ("name", "photo_file", "photo_width", "photo_height")


class CapitalAdmin(admin.ModelAdmin):
    list_display = ("name", "us_state", "date_visited", "lat", "lon")


class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "flag")


admin.site.register(Photo, PhotoAdmin)
admin.site.register(Capital, CapitalAdmin)
admin.site.register(Country, CountryAdmin)
