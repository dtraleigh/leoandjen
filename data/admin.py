from django.contrib import admin

from data.models import Water, SolarEnergy, Electricity, Gas, CarMiles, ElectricRateSchedule, AuthToken


class WaterAdmin(admin.ModelAdmin):
    ordering = ("-service_start_date",)
    list_display = [field.name for field in Water._meta.get_fields()]


class SolarAdmin(admin.ModelAdmin):
    ordering = ("-date_of_production",)
    list_display = [field.name for field in SolarEnergy._meta.get_fields()]


class ElectricityAdmin(admin.ModelAdmin):
    ordering = ("-service_start_date",)
    list_display = ["bill_date", "service_start_date", "service_end_date", "kWh_usage", "solar_amt_sent_to_grid",
                    "net_metering_credit", "calculated_money_saved_by_solar"]
    fields = ("bill_date", "service_start_date", "service_end_date", "net_metering_credit",
              "kWh_usage", "solar_amt_sent_to_grid")


class GasAdmin(admin.ModelAdmin):
    ordering = ("-service_start_date",)
    list_display = [field.name for field in Gas._meta.get_fields()]


class CarMilesAdmin(admin.ModelAdmin):
    ordering = ("-reading_date",)
    list_display = [field.name for field in CarMiles._meta.get_fields()]


class ElectricRateScheduleAdmin(admin.ModelAdmin):
    list_display = ["name", "schedule_start_date", "schedule_end_date",
                    "schedule_end_date_perpetual", "energy_charge_per_kwh", "comments"]


class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ["app", "issued_datetime"]


admin.site.register(Water, WaterAdmin)
admin.site.register(SolarEnergy, SolarAdmin)
admin.site.register(Electricity, ElectricityAdmin)
admin.site.register(Gas, GasAdmin)
admin.site.register(CarMiles, CarMilesAdmin)
admin.site.register(ElectricRateSchedule, ElectricRateScheduleAdmin)
admin.site.register(AuthToken, AuthTokenAdmin)
