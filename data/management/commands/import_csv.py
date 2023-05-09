from django.core.management.base import BaseCommand
import csv, datetime
from data.models import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        filename = "data.csv"
        rows = []

        with open(filename, "r") as csvfile:
            csvreader = csv.reader(csvfile)

            fields = next(csvreader)

            for row in csvreader:
                rows.append(row)

        for row in rows:
            # print(row)

            if row[0]:
                bill_date = datetime.datetime.strptime(row[0], "%m/%d/%Y").date()
            else:
                bill_date = None
            service_start_date = datetime.datetime.strptime(row[1], "%m/%d/%Y").date()
            service_end_date = datetime.datetime.strptime(row[2], "%m/%d/%Y").date()

            # Water.objects.create(bill_date=bill_date,
            #                      service_start_date=service_start_date,
            #                      service_end_date=service_end_date,
            #                      avg_gallons_per_day=row[3])

            # Electricity.objects.create(bill_date=bill_date,
            #                            service_start_date=service_start_date,
            #                            service_end_date=service_end_date,
            #                            kWh_usage=row[3])
            #
            Gas.objects.create(bill_date=bill_date,
                                 service_start_date=service_start_date,
                                 service_end_date=service_end_date,
                                 therms_usage=row[3])
