import logging
from datetime import datetime

from django.core.mail import mail_admins
from django.core.management.base import BaseCommand

logger = logging.getLogger("django")


class Command(BaseCommand):
    help = "Send a test email to the ADMINS in settings."

    def handle(self, *args, **options):
        n = datetime.now().strftime("%H:%M %m-%d-%y")
        logger.info(f"{n}: Trying to send email to admins")
        mail_admins("Test email", "Email from test_email.py", fail_silently=False)
        e = datetime.now().strftime("%H:%M %m-%d-%y")
        logger.info(f"{e}: Sent test email to admins")
