from django.core.management.base import BaseCommand
from data.models import *
from django.core import serializers
import datetime


class Command(BaseCommand):
    def handle(self, *args, **options):
        JSONSerializer = serializers.get_serializer("json")
        json_serializer = JSONSerializer()

        # Export water data to test_data_Water.json
        water_data = Water.objects.all()
        with open("data/test_data/test_data_Water.json", "w+") as out:
            json_serializer.serialize(water_data, stream=out)

        # Export elec data to test_data_Electricity.json
        elec_data = Electricity.objects.all()
        with open("data/test_data/test_data_Electricity.json", "w+") as out:
            json_serializer.serialize(elec_data, stream=out)

        # Export gas data to test_data_Gas.json
        gas_data = Gas.objects.all()
        with open("data/test_data/test_data_Gas.json", "w+") as out:
            json_serializer.serialize(gas_data, stream=out)

        # Export CarMiles data to test_data_CarMiles.json
        vmt_data = CarMiles.objects.all()
        with open("data/test_data/test_data_CarMiles.json", "w+") as out:
            json_serializer.serialize(vmt_data, stream=out)
