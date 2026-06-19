"""
Phase 0 characterization tests for the data app's computational core.

Snapshots the structured output of the per-year helper classes, the dashboard
builders, the average-line builder, and the DB-touching model properties against
committed golden files. Run against the JSON fixtures so results are reproducible.

See data/tests/golden_utils.py for how to (re)generate the baseline.
"""

from datetime import datetime

from django.test import TestCase

from data.functions import (
    create_avg_line_data,
    get_car_miles_all_ytd_avg,
    get_car_miles_prev_ytd,
    get_car_miles_ytd_total,
    get_elec_dashboard_data,
    get_gas_dashboard_data,
    get_vmt_dashboard_data,
    get_water_dashboard_data,
    get_years_list_from_data,
)
from data.models import CarMiles, Electricity, Gas, Water
from data.test_data.create_test_data import (
    create_test_data_elec,
    create_test_data_elec_rates,
    create_test_data_gas,
    create_test_data_solar,
    create_test_data_vmt,
    create_test_data_water,
)
from data.tests.golden_utils import CAPTURE_YEAR, assert_golden_json
from data.year_elec import ElecYear
from data.year_gas import GasYear
from data.year_vehicle_miles import VehicleMilesTraveledYear
from data.year_water import WaterYear


class GoldenCoreTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        create_test_data_water()
        create_test_data_elec_rates()
        create_test_data_elec()
        create_test_data_gas()
        create_test_data_vmt()
        create_test_data_solar()

    # --- collectors -----------------------------------------------------------

    def _collect_electricity_properties(self):
        out = {}
        for bill in Electricity.objects.order_by("pk"):
            prev = bill.get_previous_month_bill
            entry = {
                "get_number_of_days": bill.get_number_of_days,
                "get_daily_grid_usage": bill.get_daily_grid_usage,
                "get_daily_solar_send": bill.get_daily_solar_send,
                "get_total_solar_produced": bill.get_total_solar_produced,
                "get_previous_month_bill_pk": prev.pk if prev else None,
                "bill_is_lacking_rates": bill.bill_is_lacking_rates,
            }
            # get_money_saved_by_solar iterates every day with rate lookups; the
            # signals only maintain it for 2023+ bills, so scope it the same way to
            # keep the snapshot meaningful without iterating a decade of bills.
            if bill.service_start_date.year >= 2023:
                entry["get_money_saved_by_solar"] = bill.get_money_saved_by_solar
            out[bill.pk] = entry
        return out

    def _collect_carmiles_properties(self):
        return {
            r.pk: {"get_miles_per_month": r.get_miles_per_month}
            for r in CarMiles.objects.order_by("pk")
        }

    def _collect_elec_years(self):
        out = {}
        for year in get_years_list_from_data(Electricity.objects.all()) or []:
            ey = ElecYear(year, "")
            out[str(year)] = {
                "data_points": ey.get_data_points(),
                "ytd_total": ey.get_ytd_total(),
                "readings_kwh_total": ey.get_readings_kwh_total(),
                "solar_produced_total": ey.get_solar_produced_total(),
                "solar_sent_to_grid_total": ey.get_solar_sent_to_grid_total(),
                "total_house_consumed": ey.get_total_house_consumed(),
                "solar_savings_sum": ey.get_solar_savings_sum(),
                "solar_savings_table_data": ey.create_solar_savings_table_data(),
                "solar_bar_chart_dataset": ey.get_solar_bar_chart_dataset(),
                "is_lacking_energy_rates": ey.is_lacking_energy_rates(),
            }
        return out

    def _collect_simple_years(self, qs_all, year_cls):
        out = {}
        for year in get_years_list_from_data(qs_all) or []:
            obj = year_cls(year, "")
            out[str(year)] = {
                "data_points": obj.get_data_points(),
                "ytd_total": obj.get_ytd_total(),
            }
        return out

    def _collect_vmt_years(self):
        out = {}
        for year in get_years_list_from_data(CarMiles.objects.all()) or []:
            obj = VehicleMilesTraveledYear(year, "")
            out[str(year)] = {
                "data_points": obj.get_data_points(),
                "get_total_miles": obj.get_total_miles,
                "get_ytd_miles": obj.get_ytd_miles(),
            }
        return out

    # --- tests ----------------------------------------------------------------

    def test_golden_model_properties(self):
        assert_golden_json(
            self,
            "core_electricity_properties.json",
            self._collect_electricity_properties(),
        )
        assert_golden_json(
            self,
            "core_carmiles_properties.json",
            self._collect_carmiles_properties(),
        )

    def test_golden_year_classes(self):
        assert_golden_json(self, "core_elec_years.json", self._collect_elec_years())
        assert_golden_json(
            self,
            "core_gas_years.json",
            self._collect_simple_years(Gas.objects.all(), GasYear),
        )
        assert_golden_json(
            self,
            "core_water_years.json",
            self._collect_simple_years(Water.objects.all(), WaterYear),
        )
        assert_golden_json(self, "core_vmt_years.json", self._collect_vmt_years())

    def test_golden_dashboards_and_avg_lines(self):
        # Pass an explicit current_date so the dashboards are clock-independent.
        current_date = datetime(CAPTURE_YEAR, 1, 1)
        dashboards = {
            "elec": get_elec_dashboard_data(current_date=current_date),
            "gas": get_gas_dashboard_data(current_date=current_date),
            "water": get_water_dashboard_data(current_date=current_date),
            "vmt": get_vmt_dashboard_data(),
        }
        assert_golden_json(self, "core_dashboards.json", dashboards)

        avg_lines = {
            name: create_avg_line_data(name)
            for name in ("Electricity", "Gas", "Water", "CarMiles")
        }
        assert_golden_json(self, "core_avg_lines.json", avg_lines)

        car_miles_helpers = {
            "ytd_total": get_car_miles_ytd_total(),
            "prev_ytd": get_car_miles_prev_ytd(),
            "all_ytd_avg": get_car_miles_all_ytd_avg(),
        }
        assert_golden_json(self, "core_car_miles_helpers.json", car_miles_helpers)
