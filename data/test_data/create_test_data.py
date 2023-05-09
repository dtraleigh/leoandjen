"""
When running tests, these are used to populate the test database. The JSON files are serialized exports
taken from the app itself.
"""

from django.core import serializers


def create_test_data_water():
    with open("data/test_data/test_data_Water.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()


def create_test_data_elec():
    with open("data/test_data/test_data_Electricity.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()


def create_test_data_gas():
    with open("data/test_data/test_data_Gas.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()


def create_test_data_vmt():
    # snapshot as of Feb 3, 2023
    with open("data/test_data/test_data_CarMiles.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()
