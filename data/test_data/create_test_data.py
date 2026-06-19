"""
When running tests, these are used to populate the test database. The JSON files are serialized exports
taken from the app itself.
"""

from django.core import serializers


def create_test_data_water():
    with open("data/test_data/test_data_Water.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()


def create_test_data_elec_rates():
    with open("data/test_data/test_data_ElectricRateSchedule.json") as jsonfile:
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


def create_test_data_solar():
    # Deterministic daily solar production for 2023 (the period where the
    # Electricity fixtures start sending solar to the grid). Without this,
    # all solar aggregation paths are exercised against an empty table.
    with open("data/test_data/test_data_SolarEnergy.json") as jsonfile:
        for obj in serializers.deserialize("json", jsonfile):
            obj.save()
