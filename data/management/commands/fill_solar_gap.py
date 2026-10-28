import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from data.models import SolarEnergy

logger = logging.getLogger("django")


def get_source_date(gap_date):
    """Returns the same calendar day one year earlier. Feb 29 maps to Feb 28."""
    if gap_date.month == 2 and gap_date.day == 29:
        return gap_date.replace(year=gap_date.year - 1, day=28)
    return gap_date.replace(year=gap_date.year - 1)


class Command(BaseCommand):
    help = ("One-off fill of lost solar data using the same day from the year before. "
            "Example: fill_solar_gap -s 2026-08-20 -e 2026-10-08 -t")

    def add_arguments(self, parser):
        parser.add_argument("-s", "--start", required=True, help="gap start date, format YYYY-MM-DD")
        parser.add_argument("-e", "--end", required=True, help="gap end date, format YYYY-MM-DD")
        parser.add_argument("-t", "--test", action="store_true", help="Run a test, no changes made.")

    def handle(self, *args, **options):
        start_date = datetime.strptime(options["start"], "%Y-%m-%d").date()
        end_date = datetime.strptime(options["end"], "%Y-%m-%d").date()
        is_test = options["test"]

        filled = []
        skipped_real_data = []
        no_source = []

        with transaction.atomic():
            gap_date = start_date
            while gap_date <= end_date:
                existing = SolarEnergy.objects.filter(date_of_production=gap_date).first()
                if existing and existing.production > 0:
                    print(f"{gap_date} already has {existing.production}, skipping.")
                    skipped_real_data.append(gap_date)
                    gap_date += timedelta(days=1)
                    continue

                source_date = get_source_date(gap_date)
                source = SolarEnergy.objects.filter(date_of_production=source_date).first()
                if not source or source.production == 0:
                    print(f"No usable data on {source_date} to fill {gap_date}.")
                    no_source.append(gap_date)
                    gap_date += timedelta(days=1)
                    continue

                if is_test:
                    print(f"Fake filling {gap_date} with {source.production} from {source_date}")
                else:
                    if existing:
                        existing.production = source.production
                        existing.save(update_fields=["production"])
                    else:
                        SolarEnergy.objects.create(date_of_production=gap_date, production=source.production)
                    logger.info(f"{datetime.now()}: Filled {gap_date} with {source.production} from {source_date}")
                filled.append(gap_date)
                gap_date += timedelta(days=1)

        prefix = "[TEST] Would have filled" if is_test else "Filled"
        print(f"{prefix} {len(filled)} day(s). Skipped {len(skipped_real_data)} day(s) that already had data.")
        if no_source:
            print(f"No usable source data for {len(no_source)} day(s): "
                  f"{', '.join(day.strftime('%Y-%m-%d') for day in no_source)}")
