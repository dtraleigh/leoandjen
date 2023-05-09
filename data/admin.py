from django.contrib import admin
from data.models import *


class WaterAdmin(admin.ModelAdmin):
    ordering = ("-service_start_date",)
    list_display = [field.name for field in Water._meta.get_fields()]


class SolarAdmin(admin.ModelAdmin):
    ordering = ("-date_of_production",)
    list_display = [field.name for field in SolarEnergy._meta.get_fields()]


class ElectricityAdmin(admin.ModelAdmin):
    ordering = ("-service_start_date",)
    list_display = [field.name for field in Electricity._meta.get_fields()]


class GasAdmin(admin.ModelAdmin):
    ordering = ("-service_start_date",)
    list_display = [field.name for field in Gas._meta.get_fields()]


class CarMilesAdmin(admin.ModelAdmin):
    ordering = ("-reading_date",)
    list_display = [field.name for field in CarMiles._meta.get_fields()]


admin.site.register(Water, WaterAdmin)
admin.site.register(SolarEnergy, SolarAdmin)
admin.site.register(Electricity, ElectricityAdmin)
admin.site.register(Gas, GasAdmin)
admin.site.register(CarMiles, CarMilesAdmin)
