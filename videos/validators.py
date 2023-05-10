import os

from django.core.exceptions import ValidationError


def validate_poster_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".jpg", ".png", ".gif", "jpeg"]
    if not ext in valid_extensions:
        raise ValidationError("Not a supported image format.")


def validate_video_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".mp4", ".m4v"]
    if not ext in valid_extensions:
        raise ValidationError("Not a supported video file type.")
