"""
Characterization-test helpers (Phase 0 of the query-efficiency refactor).

The idea: capture the CURRENT output of the data app's computational core and its
rendered pages into committed "golden" files, then assert future code produces the
exact same output. This pins behavior so the upcoming query optimizations can be
proven behavior-preserving.

Regenerate the golden files (only intentionally — e.g. to establish the baseline on
an unchanged tree, or to accept a deliberate behavior change) with:

    UPDATE_GOLDEN=1 python manage.py test data.tests.test_golden_core data.tests.test_golden_views

Without that env var the same tests COMPARE live output against the committed files.
"""

import datetime
import json
import os
import re
from decimal import Decimal
from pathlib import Path

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

# True when we are (re)writing the golden files instead of asserting against them.
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"

# Several dashboard helpers fold in "the current year". Only the calendar *year* is
# ever read, so snapshots are stable within a year but must be re-baselined if the
# year rolls over. The view tests guard on this; core tests pass an explicit date.
CAPTURE_YEAR = 2026

# Floats (Python average/division results) are rounded before comparison so we don't
# fail on sub-microscopic noise while still catching any real numeric change.
_FLOAT_PRECISION = 6


def normalize(obj):
    """Recursively convert a value into a deterministic, JSON-serializable form.

    Non-JSON types are tagged so a type change (e.g. Decimal -> float) is still
    visible as a diff rather than silently collapsing to the same text.
    """
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, Decimal):
        return f"Decimal:{obj}"
    if isinstance(obj, datetime.timedelta):
        return f"timedelta:{obj.days}d{obj.seconds}s"
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, float):
        return round(obj, _FLOAT_PRECISION)
    if isinstance(obj, dict):
        return {str(k): normalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [normalize(v) for v in obj]
    return obj


def _canonical(data):
    return json.dumps(normalize(data), indent=2, sort_keys=True, ensure_ascii=False)


def assert_golden_json(test, name, data):
    """Compare a structured Python value against golden/<name> (or write it)."""
    path = GOLDEN_DIR / name
    current = _canonical(data)

    if UPDATE:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(current + "\n", encoding="utf-8")
        return

    test.assertTrue(
        path.exists(),
        f"Golden file missing: {path}. Create the baseline with "
        f"UPDATE_GOLDEN=1 python manage.py test ...",
    )
    expected = path.read_text(encoding="utf-8").rstrip("\n")
    test.assertMultiLineEqual(
        expected,
        current,
        msg=f"\nOutput diverged from golden '{name}'. If this change is intentional, "
        f"re-baseline with UPDATE_GOLDEN=1.",
    )


_CSRF_RE = re.compile(r'name="csrfmiddlewaretoken"\s+value="[^"]*"')


def normalize_html(html):
    """Strip the handful of non-deterministic bits from rendered HTML."""
    html = _CSRF_RE.sub('name="csrfmiddlewaretoken" value="__STRIPPED__"', html)
    return html.strip()


def assert_golden_text(test, name, text):
    """Compare normalized text (e.g. rendered HTML) against golden/<name>."""
    path = GOLDEN_DIR / name
    current = normalize_html(text)

    if UPDATE:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(current + "\n", encoding="utf-8")
        return

    test.assertTrue(
        path.exists(),
        f"Golden file missing: {path}. Create the baseline with "
        f"UPDATE_GOLDEN=1 python manage.py test ...",
    )
    expected = path.read_text(encoding="utf-8").rstrip("\n")
    test.assertMultiLineEqual(
        expected,
        current,
        msg=f"\nRendered HTML diverged from golden '{name}'. If intentional, "
        f"re-baseline with UPDATE_GOLDEN=1.",
    )
