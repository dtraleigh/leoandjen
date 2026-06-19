# Data App — Database Query Efficiency Plan

## Context

The `data` app (a household utilities tracker: electricity, gas, water, solar, car
miles) works correctly but some pages render slower than they should in the browser.
The root cause is **not** missing `select_related`/`prefetch_related` on FKs (the models
are mostly flat with few relations) — it's that the app recomputes everything on every
request by:

1. **Re-querying the DB inside Python loops** (per-bill, per-month, per-day, per-reading)
   instead of using set-based queries and DB aggregation.
2. **Model `@property` methods that issue their own queries** and are then called inside
   loops in templates and in the `*Year` helper classes — classic N+1.
3. **`*Year` helper objects that re-run their queries every time a method is called**,
   with no memoization, and that are instantiated **once per year of history** on the
   dashboard.

Scope: **read/page-browse path only** (not the save-path signals). Schema
changes/denormalization are **on the table**. **No caching layer** — fix the underlying
queries instead.

### Key files
- `data/views.py` — `home`, `electricity`, `water`, `gas`, `car_miles`
- `data/functions.py` — dashboard builders, `create_avg_line_data`, year/aggregate helpers
- `data/year_elec.py`, `data/year_gas.py`, `data/year_water.py`, `data/year_vehicle_miles.py`
- `data/models/electricity.py`, `data/models/carMiles.py`
- Templates: `elec.html`, `page.html`, `miles.html`, `data_base.html`, `data_home.html`

### How to measure (do this first and after each tier)
- Add `django-debug-toolbar` locally (dev settings only) to see per-page query counts, or
  wrap a view in `django.test.utils.CaptureQueriesContext` / log `len(connection.queries)`.
- Lock in wins with `assertNumQueries` tests around `home()`, `electricity()`, and
  `car_miles()` so regressions are caught.

---

## Phase 0 — Characterization safety net (build BEFORE any change)

Goal: prove the refactor is behavior-preserving. We capture the current outputs into
committed "golden" files now, then assert post-refactor outputs match exactly. This is
the same technique already used by `test_elec_usage_for_2022` (`test_electricity.py:154`)
and `test_car_miles_get_data_points` (`test_carMiles.py:45`) — extended to full coverage
and automated. All of it runs against the existing `test_data_*.json` fixtures, so it is
reproducible without the production DB.

### Prerequisites
1. **Add a `SolarEnergy` fixture.** No solar test data exists today, so every elec golden
   value has `solar_produced = 0.00` and the solar aggregation paths
   (`Electricity.get_total_solar_produced`, `ElecYear.get_total_solar_produced_by_month`,
   `get_solar_bar_chart_dataset`) are **completely uncovered**. Tier 1 #2, Tier 2 #3, and
   Tier 3 #1 all rewrite that code, so we add `data/test_data/test_data_SolarEnergy.json`
   (covering the elec service dates in the fixtures) and load it alongside the others.
2. **Freeze time.** Dashboard builders, `clean_year_range_request("all")`,
   `get_cards_for_the_year`, and YTD "latest" logic call `datetime.now()`/`timezone.now()`.
   Generation and comparison must run under a fixed date (`freezegun.freeze_time`, or pass
   the existing `current_date=` params) or snapshots drift day to day.

### Layer 1 — Computational core (golden JSON snapshots)
A generator (management command `dump_golden`, or a test helper) loads the fixtures and
serializes, for every year present in the data:
- `ElecYear`/`GasYear`/`WaterYear`/`VehicleMilesTraveledYear`: `get_data_points()`,
  `get_ytd_total()`, plus elec extras (`get_readings_kwh_total`, `get_solar_produced_total`,
  `get_solar_sent_to_grid_total`, `get_total_house_consumed`, `get_solar_savings_sum`,
  `create_solar_savings_table_data`, `get_solar_bar_chart_dataset`, `is_lacking_energy_rates`).
- `functions.py`: `get_elec/gas/water/vmt_dashboard_data()`, `create_avg_line_data()` per
  class, `get_years_list_from_data()`.
- Model properties per record: `Electricity.get_total_solar_produced`,
  `get_money_saved_by_solar`, `get_number_of_days`, `bill_is_lacking_rates`;
  `CarMiles.get_miles_per_month`.

Output written to `data/tests/golden/*.json` (Decimals serialized as strings to compare
exactly). Committed as the pre-change baseline.

### Layer 2 — End-to-end view snapshots
Django `test.Client` GETs each route (`/`, `/data/electricity/`, `/data/gas/`,
`/data/water/`, `/data/car_miles/`) under frozen time with several `?years=` values
(`all`, default, a single year). Snapshot the normalized rendered HTML to
`data/tests/golden/views/`. Identical HTML body = identical rendered numbers/charts.

### Layer 3 — Query-count baselines
Wrap the same view GETs in `assertNumQueries` (baseline counts recorded now). After each
tier the optimized pages must show **fewer** queries and no page may increase.

### Test files (IMPLEMENTED)
- `data/tests/golden_utils.py` — `normalize`/`assert_golden_json`/`assert_golden_text`
  helpers; `UPDATE_GOLDEN` env flag toggles write-vs-compare; `CAPTURE_YEAR` guard.
- `data/tests/test_golden_core.py` — snapshots year classes, dashboards, avg lines, and
  model properties to `data/tests/golden/core_*.json`.
- `data/tests/test_golden_views.py` — snapshots rendered HTML to
  `data/tests/golden/views/*.html` and query counts to `view_query_counts.json`.
- `data/test_data/test_data_SolarEnergy.json` + `create_test_data_solar()` — daily 2023
  solar fixture so solar aggregation is actually exercised.

Regeneration is via the `UPDATE_GOLDEN=1` env var (the isolated test DB guarantees
fixture-based determinism), not a management command:
`UPDATE_GOLDEN=1 python manage.py test data.tests.test_golden_core data.tests.test_golden_views`

### Captured baseline query counts (pre-refactor, `?years=all` where noted)
`electricity_all = 2649`, `electricity_2022 = 1433`, `home = 825`,
`car_miles_all = 258`, `water_all = 136`, `gas_all = 40`. These are the targets the
tiers must drive down; `test_golden_views` fails if any page regresses above its baseline.

### Workflow
1. ✅ Harness + fixtures built; baseline captured and committed on current `main`.
2. ✅ `manage.py test data` is green (45 tests) — baseline passes against itself, and a
   deliberate perturbation was confirmed to fail (the net actually catches drift).
3. Do the refactor tiers; the golden tests must stay green and query counts must drop.
   Any HTML/value diff = a deliberate decision (real bug fix) or a regression to undo.
   Re-baseline only on purpose with `UPDATE_GOLDEN=1`.

> Note: golden tests pin *current* behavior, including any latent bugs — intentional. The
> objective is "no behavior change," so a changed value forces a conscious choice.

---

## Tier 1 — Easy / Low impact (quick, low-risk, do first)

> ✅ **DONE.** Behavior preserved (golden core + view HTML byte-identical; all 45 tests
> green). Query counts: **home 825 → 662 (−163), electricity?years=all 2649 → 2541
> (−108), electricity?years=2022 1433 → 1420 (−13)**; gas/water/car_miles unchanged (no
> regression). Count wins come from the memoization (#1); #2 and #3 mainly cut data volume
> (same query count). Baseline re-locked to the new numbers. Item #4 was a no-op — see below.

Small, local edits. Each removes redundant queries without changing behavior or schema.

1. **Memoize `get_data_points()` in the `*Year` classes.**
   `__init__` already computes `self.data_points = self.get_data_points()` (e.g.
   `year_elec.py:25`), but other methods call `self.get_data_points()` *again*, re-running
   all the queries: `ElecYear.get_ytd_total()` (`year_elec.py:92`) and
   `get_solar_bar_chart_dataset()` (`year_elec.py:167`). Change these to use the cached
   `self.data_points`. Apply the same pattern in `year_gas.py`, `year_water.py`.

2. **Make `Electricity.get_total_solar_produced` aggregate in the DB.**
   `data/models/electricity.py:92-97` pulls every `SolarEnergy` row and sums in Python.
   Replace with `.aggregate(Sum("production"))` — the correct pattern already exists in
   `ElecYear.get_total_solar_produced_by_month` (`year_elec.py:101-110`). One query, no
   Python loop.

3. **Stop loading full objects just to extract years.**
   `get_*_dashboard_data` in `functions.py` (lines ~254-255, 284-285, 315-316) call
   `Model.objects.all()` **twice** and comprehend years in Python. Replace with
   `Model.objects.dates("service_start_date", "year")` (or
   `.values_list("service_start_date__year", flat=True).distinct()`), unioned with the end
   date. Same idea for `get_years_list_from_data` (`functions.py:29-50`).

4. **~~Avoid `getattr`-triggered property queries in `export_csv`.~~** No-op: the view
   already iterates only `model._meta.fields + many_to_many` (concrete fields, no
   DB-querying properties), and the route is commented out in `urls.py`. Left unchanged.

**Payoff:** removes the duplicate `.all()` scans on every dashboard load and the repeated
`get_data_points()` re-runs; turns a per-row solar scan into one aggregate.

---

## Tier 2 — Medium effort / Mid impact

> ✅ **DONE.** Behavior preserved (golden core + view HTML byte-identical; all 45 tests
> green). Query counts after Tier 2 (vs Tier 1 baseline): **electricity?years=all 2541 →
> 270 (−89%), electricity?years=2022 1420 → 132, home 662 → 224, car_miles 258 → 37,
> water 136 → 40, gas 40 → 16.** Implementation notes:
> - #1 `create_avg_line_data` now indexes each year's cached `data_points` once instead of
>   calling `get_data_points()` 12×/year.
> - #2 new `CarMiles.get_miles_per_month_map()` (one query) backs `VehicleMilesTraveledYear`,
>   the CarMiles avg line, and the miles table (view precomputes `row.miles_this_month`; the
>   `get_miles_per_month` property is kept for direct/test use).
> - #3 `ElecYear.get_solar_produced_total` now sums all readings' solar in one `Q`-OR
>   aggregate query and memoizes the result.
> - #4 `Electricity.bill_is_lacking_rates` resolves storm-recovery coverage from one fetched
>   schedule list instead of a query per day; passes the existing rate-coverage tests.
> - #5 `ElecYear.is_lacking_energy_rates` is now lazy (removed from `__init__`) + memoized,
>   so the dashboard's per-year `*Year` objects no longer pay for it. (Deeper "YTD via pure
>   SQL" is left to Tier 3.) Baseline re-locked to the new numbers.

Restructuring loops and N+1 properties into batched, set-based queries. No schema change.

1. **Fix the `create_avg_line_data` nested re-query (biggest single read-path win).**
   `functions.py:179-189` loops `for month in 1..12:` and inside it
   `for year in yearly_objects: year.get_data_points()` — so `get_data_points()` runs
   **12×N** times, each a full query set. Invert it: call `get_data_points()` **once per
   year** (or rely on the Tier 1 memoized `self.data_points`), build a `{month: value}`
   index, then assemble the averages. Reduces electricity/gas/water chart pages from
   ~12×years queries to ~years.

2. **Kill the `CarMiles.get_miles_per_month` N+1.**
   `data/models/carMiles.py:29-39` does a `.get()` for the *next* month per reading; it's
   called per-row in `miles.html:53-59`, in `VehicleMilesTraveledYear`, and in
   `create_avg_line_data` (`functions.py:202`). Fetch the relevant readings once (already
   ordered by `reading_date`) and compute consecutive differences in Python (`zip(rows,
   rows[1:])`), or annotate with `Window(Lead("odometer_reading"))`. Have the view pass the
   precomputed per-reading miles to the template instead of the property.

3. **Batch the solar lookups behind `ElecYear.get_solar_produced_total`.**
   `year_elec.py:148-151` sums `t.get_total_solar_produced` per reading → one
   `SolarEnergy` query per bill. Replace with a single `SolarEnergy` query spanning the
   year's service range, aggregated (reuse the by-month aggregate already in the class).

4. **Replace the per-day rate-coverage loops with set-based checks.**
   `Electricity.bill_is_lacking_rates` (`electricity.py:156-175`) and
   `ElecYear.is_lacking_energy_rates` (`year_elec.py:180-184`) issue queries per day per
   bill. A bill is "lacking rates" iff there's an uncovered day — compute coverage with a
   couple of range queries against `ElectricRateSchedule` over the whole service period
   instead of iterating `timedelta(days=1)`.

5. **Compute dashboard YTD totals with targeted queries, not full `*Year` objects.**
   `get_elec/gas/water_dashboard_data` build a `*Year` object for **every year in history**
   just to read `get_ytd_total()` for the last two years + an average. Most of those
   objects' work is thrown away. Compute YTD via direct aggregate queries, or only
   instantiate the years actually needed.

**Payoff:** the chart/list pages and the dashboard drop from "queries scale with
months×years×bills" to "a handful of aggregate queries."

---

## Tier 3 — Big effort / High impact (structural)

Addresses the architecture: the `*Year` classes do per-bill/per-month iteration that
should be single grouped queries, and several read-time computations should be stored.

1. **Reduce each `*Year` to a fixed, small query count via grouped aggregation.**
   `ElecYear.get_data_points` (`year_elec.py:31-79`) loops every bill × every month calling
   `get_number_of_days_in_month`, `get_daily_solar_send`, etc., then queries `SolarEnergy`
   once per month (`get_total_solar_produced_by_month`, 12 queries/year). Rework to:
   - one `SolarEnergy` query per year grouped by month (`TruncMonth` + `annotate(Sum)`),
   - one `Electricity` query per year, with monthly allocation done in Python on already
     fetched rows.
   This is the core change; apply the same shape to `GasYear`/`WaterYear`/`VehicleMilesTraveledYear`.

2. **Denormalize read-time computed values (schema change — approved).**
   - `calculated_money_saved_by_solar` already exists and is maintained by signals — make
     the read path (`get_solar_savings_sum`, `elec.html`) read it directly and never call
     the live `get_money_saved_by_solar` property during rendering.
   - Add a stored per-bill `solar_produced_kwh` (and optionally monthly solar rollups)
     populated on bill/solar save, so `get_total_solar_produced` becomes a column read.
     Include a data migration + a management command to backfill.
   This removes the remaining N+1 properties from the render path entirely.

3. **(Optional, related) Trim the save-path signals so they don't compound.**
   Out of declared scope (save path), but noted: `update_money_saved_by_solar_on_instance`
   and the `ElectricRateSchedule` post_save (`electricity.py:185-263`) both call
   `associate_elec_bills_to_rates()` (nested bills×schedules loop, `functions.py:470-490`)
   and recompute *all* 2023+ bills on every single save. If uploads ever feel slow, this is
   why. Flagging only — no action unless scope expands.

**Payoff:** dashboard and every chart/list page become a small constant number of queries
regardless of how many years/bills/solar-days accumulate.

---

## Suggested order
1. Tier 1 (1-2 hrs, immediate redundant-query removal).
2. Add `assertNumQueries` baselines for `home`, `electricity`, `car_miles`.
3. Tier 2 #1 and #2 (avg-line re-query + car-miles N+1) — best effort:payoff ratio.
4. Remaining Tier 2.
5. Tier 3 #1 (grouped aggregation) then #2 (denormalization w/ migration + backfill).

## Verification
- Before/after query counts per page via debug-toolbar or `CaptureQueriesContext`.
- `assertNumQueries` regression tests on the three main views.
- Manually load `/` (dashboard), `/data/electricity`, `/data/water`, `/data/gas`,
  `/data/car_miles` with `?years=all` and confirm identical rendered numbers/charts plus
  lower query counts and faster load.