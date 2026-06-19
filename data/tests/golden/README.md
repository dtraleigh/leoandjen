# Golden (characterization) baselines

These files are the committed reference output for the data app's
characterization tests (`data/tests/test_golden_core.py` and
`data/tests/test_golden_views.py`). They were captured to lock in behavior while
the DB-query optimizations in `data/OPTIMIZATION_PLAN.md` were applied, and they
guard against regressions going forward. **Keep them committed** — the tests
compare live output against these files, so without them there is no safety net.

- `core_*.json` — structured output of the `*Year` classes, dashboard builders,
  average-line builder, and DB-touching model properties.
- `views/*.html` — rendered HTML of each public page (CSRF tokens stripped).
- `view_query_counts.json` — the per-page DB query-count ceiling. The view test
  fails if any page exceeds its number, so it catches query regressions.

## Running

```
python manage.py test data.tests.test_golden_core data.tests.test_golden_views
```

## Regenerating (only on purpose)

Regenerate after an *intended* behavior change, or to lower the query-count
ceiling after a confirmed optimization:

```
UPDATE_GOLDEN=1 python manage.py test data.tests.test_golden_core data.tests.test_golden_views
```

Review the resulting diff before committing — an unexpected change here means a
behavior change, not noise.

## Notes

- Determinism comes from the JSON fixtures in `data/test_data/` (including
  `test_data_SolarEnergy.json`, which must stay committed so the solar paths are
  exercised).
- The snapshots are pinned to `CAPTURE_YEAR` (see `golden_utils.py`); the view
  tests auto-skip with a "re-baseline" message if run in a later calendar year,
  because some dashboard logic folds in the current year.
