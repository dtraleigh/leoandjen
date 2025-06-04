from datetime import timedelta
from django.utils import timezone

from django.db import models


class AuthToken(models.Model):
    name = models.CharField(max_length=200)
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200)
    app_code = models.CharField(max_length=200)
    redirect_uri = models.CharField(max_length=200)
    access_token = models.CharField(max_length=1024)
    refresh_token = models.CharField(max_length=1024)
    issued_datetime = models.DateTimeField(auto_now=True)
    expires_in = models.IntegerField(default=1000)

    def __str__(self):
        return f"{self.id}"

    def is_token_expired(self, buffer=0):
        """
        Checks if the token is expired or will expire within the given buffer time.
        Returns True if expired or about to expire (considering the buffer), False otherwise.
        """
        expiration_time = self.issued_datetime + timedelta(seconds=self.expires_in)
        expiration_with_buffer = expiration_time - timedelta(seconds=buffer)
        return expiration_with_buffer <= timezone.now()