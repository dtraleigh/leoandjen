"""
Phase 0 characterization tests for the data app's rendered pages, plus query-count
baselines.

- The rendered HTML of each public GET page is snapshotted, so the refactor must
  produce byte-identical output (after stripping CSRF tokens).
- The number of DB queries per page is recorded as a baseline. The refactor must not
  INCREASE any page's query count; the optimized pages are expected to drop well below
  their baseline (update the baseline intentionally when that happens).

See data/tests/golden_utils.py for how to (re)generate the baselines.
"""

import json
from datetime import datetime

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from data.test_data.create_test_data import (
    create_test_data_elec,
    create_test_data_elec_rates,
    create_test_data_gas,
    create_test_data_solar,
    create_test_data_vmt,
    create_test_data_water,
)
from data.tests.golden_utils import (
    CAPTURE_YEAR,
    GOLDEN_DIR,
    UPDATE,
    assert_golden_text,
)

QUERY_COUNT_FILE = GOLDEN_DIR / "view_query_counts.json"

# (case name, url name, query string). The case name is the golden HTML filename stem.
VIEW_CASES = [
    ("home", "data:home", ""),
    ("electricity_all", "data:electricity", "?years=all"),
    ("electricity_2022", "data:electricity", "?years=2022"),
    ("gas_all", "data:gas", "?years=all"),
    ("water_all", "data:water", "?years=all"),
    ("car_miles_all", "data:car_miles", "?years=all"),
]


class GoldenViewsTestCase(TestCase):
    databases = "__all__"

    @classmethod
    def setUpTestData(cls):
        create_test_data_water()
        create_test_data_elec_rates()
        create_test_data_elec()
        create_test_data_gas()
        create_test_data_vmt()
        create_test_data_solar()

    def setUp(self):
        # Dashboards/range-defaults fold in the current calendar year, so the golden
        # HTML is only valid for the year it was captured in.
        if datetime.now().year != CAPTURE_YEAR:
            self.skipTest(
                f"Golden view snapshots were captured for {CAPTURE_YEAR}; current year "
                f"is {datetime.now().year}. Re-baseline with UPDATE_GOLDEN=1."
            )

    def test_golden_views(self):
        counts = {}
        for name, url_name, query in VIEW_CASES:
            url = reverse(url_name) + query
            with CaptureQueriesContext(connection) as ctx:
                response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, f"{name} ({url}) returned {response.status_code}"
            )
            counts[name] = len(ctx)
            assert_golden_text(
                self, f"views/{name}.html", response.content.decode("utf-8")
            )

        self._check_query_counts(counts)

    def _check_query_counts(self, counts):
        if UPDATE:
            QUERY_COUNT_FILE.parent.mkdir(parents=True, exist_ok=True)
            QUERY_COUNT_FILE.write_text(
                json.dumps(counts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return

        self.assertTrue(
            QUERY_COUNT_FILE.exists(),
            f"Missing {QUERY_COUNT_FILE}. Baseline with UPDATE_GOLDEN=1.",
        )
        baseline = json.loads(QUERY_COUNT_FILE.read_text(encoding="utf-8"))
        for name, count in counts.items():
            self.assertIn(name, baseline, f"No query-count baseline for '{name}'.")
            self.assertLessEqual(
                count,
                baseline[name],
                msg=(
                    f"\nPage '{name}' now runs {count} queries vs baseline "
                    f"{baseline[name]} — a regression. Investigate, or lower the "
                    f"baseline intentionally with UPDATE_GOLDEN=1 if this is expected."
                ),
            )
            # Surface the win in test output without failing.
            if count < baseline[name]:
                print(
                    f"[query-count] {name}: {count} (was {baseline[name]}, "
                    f"-{baseline[name] - count})"
                )
