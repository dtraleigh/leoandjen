import logging
from datetime import datetime

import requests
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from data.models import AuthToken

logger = logging.getLogger("django")

class Command(BaseCommand):
    help = "Refresh OAuth tokens for all applications"

    def handle(self, *args, **options):
        logger.info(f"{datetime.now()}: Starting token refresh process...")
        success_count = 0
        fail_count = 0

        for app in AuthToken.objects.all():
            logger.info(f"{datetime.now()}: Checking token for app: {app.name}")
            # Check if token needs refreshing
            if app.is_token_expired(buffer=3600):  # Refresh if less than 1 hour left
                logger.info(f"{datetime.now()}: Token for app '{app.name}' is nearing expiration. Refreshing...")
                try:
                    response = requests.post(
                        "https://api.enphaseenergy.com/oauth/token",
                        data={
                            "grant_type": "refresh_token",
                            "client_id": app.client_id,
                            "client_secret": app.client_secret,
                            "refresh_token": app.refresh_token,
                        },
                    )

                    if response.status_code == 200:
                        token_data = response.json()
                        app.access_token = token_data["access_token"]
                        app.refresh_token = token_data.get("refresh_token", app.refresh_token)
                        app.expires_in = token_data["expires_in"]
                        app.issued_datetime = now()
                        app.save()
                        logger.info(f"Token for app '{app.name}' refreshed successfully.")
                        success_count += 1
                    else:
                        logger.info(f"{datetime.now()}: "
                            f"Failed to refresh token for app '{app.name}'. "
                            f"Response: {response.json()}"
                        )
                        fail_count += 1

                except Exception as e:
                    self.stderr.write(
                        f"An error occurred while refreshing token for app '{app.name}': {str(e)}"
                    )
                    fail_count += 1
            else:
                logger.info(f"{datetime.now()}: Token for app '{app.name}' is still valid.")

        logger.info(f"{datetime.now()}: "
            f"Token refresh process completed. Success: {success_count}, Failures: {fail_count}."
        )
