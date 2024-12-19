import logging
from datetime import datetime, timedelta
from data.enphase import *
from django.db.models import Max

from django.core.management.base import BaseCommand

from data.models import SolarEnergy, AuthToken

logger = logging.getLogger("django")

def get_yesterdays_date():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday


def get_last_production_date():
    """Returns the date of the most recent SolarEnergy instance"""
    last_date = SolarEnergy.objects.aggregate(Max('date_of_production'))['date_of_production__max']
    return last_date if last_date else None


class Command(BaseCommand):
    help = "Example: solar_data -s 2023-01-31 -e 2023-02-08"

    def add_arguments(self, parser):
        # Optional arguments
        parser.add_argument("-s", "--start", help="start date, format YYYY-MM-DD")
        parser.add_argument("-e", "--end", help="end date, format YYYY-MM-DD")
        parser.add_argument("-t", "--test", action="store_true", help="Run a test, no changes made.")
        parser.add_argument("-a", "--auto_dates", action="store_true", help="Auto set the dates.")

    def handle(self, *args, **options):
        start_date = options["start"]
        end_date = options["end"]
        is_test = options["test"]
        auto_dates = options["auto_dates"]

        enphase_auth = AuthToken.objects.get(name=env("AUTH_APP_NAME"))
        logger.info(f"{datetime.now()}: Checking token expiration for app {enphase_auth.name}...")
        if is_token_expired(enphase_auth):
            logger.info(f"{datetime.now()}: Access token expired. Refreshing...")
            refresh_access_token(env("ENPHASE_CLIENT_ID"),
                                 env("ENPHASE_CLIENT_SECRET"),
                                 enphase_auth.refresh_token,
                                 enphase_auth)

        if auto_dates:
            start_date = get_last_production_date() + timedelta(days=1)
            start_date = start_date.strftime('%Y-%m-%d')
            end_date = get_yesterdays_date().strftime('%Y-%m-%d')
            site_data = get_site_production(enphase_auth.access_token, start_date, end_date)
        else:
            site_data = get_site_production(enphase_auth.access_token, start_date, end_date)

        # Add new solar data to SolarEnergy models
        try:
            if start_date == site_data["start_date"]:
                start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
                production_amts = get_production_amts(site_data)

                for day_amt in production_amts:
                    if SolarEnergy.objects.filter(date_of_production=start_date_dt).exists():
                        # Just check that the production numbers match
                        production_object = SolarEnergy.objects.get(date_of_production=start_date_dt)
                        if production_object.production != day_amt:
                            print(
                                f"For {production_object.date_of_production.strftime('%Y-%m-%d')}, DB has {production_object.production} where API reports {day_amt}")
                        else:
                            print(f"Data for {start_date_dt} already exists.")
                    else:
                        # Create a new object
                        if not is_test:
                            SolarEnergy.objects.create(date_of_production=start_date_dt,
                                                       production=day_amt)
                            logger.info(f"{datetime.now()}: Creating new SolarEnergy day for {start_date_dt}, amt: {day_amt}")
                        else:
                            print(f"Fake creating new SolarEnergy day for {start_date_dt}, amt: {day_amt}")
                    # Increment the date
                    start_date_dt += timedelta(days=1)

            else:
                print(f"Please check start date input versus data start_date of {site_data['start_date']}")
        except KeyError:
            print(site_data)
            print(f"start_date: {start_date}")
            print(f"end_date: {end_date}")
