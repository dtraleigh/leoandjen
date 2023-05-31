from ckeditor.fields import RichTextField
from django.db import models
from django.urls import reverse

from videos.validators import (validate_poster_extension,
                               validate_video_extension)


class Video(models.Model):
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Date added")
    name = models.CharField(max_length=200)
    date_shot = models.DateField(verbose_name="Date taken")
    poster = models.FileField(upload_to="poster/%Y/%m/", validators=[validate_poster_extension])
    video_file = models.FileField(upload_to="video/%Y/%m/", validators=[validate_video_extension])
    description = models.TextField(default=None, blank=True, null=True)
    rich_description = RichTextField(default="", blank=True, null=True)
    tags = models.ManyToManyField("Tag", default=None, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0)

    # Videos are ordered in descending order by the date they were taken. (newest to oldest)
    class Meta:
        ordering = ["-date_shot"]

    def __str__(self):
        return f"{self.name}, taken on {self.date_shot}"

    def get_cname(self):
        return self.__class__.__name__

    def get_tags(self):
        return "\n".join([p.name for p in self.tags.all()])

    def get_absolute_url(self):
        return reverse("recent_shot", args=["video", self.id])

    def delete(self):
        self.video_file.delete()
        self.poster.delete()
        super().delete()


class ExternalVideo(models.Model):
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Date added")
    name = models.CharField(max_length=200)
    date_shot = models.DateField(verbose_name="Date taken")
    embed_code = models.TextField(default=None, blank=True, null=True)
    poster = models.FileField(upload_to="poster/%Y/%m/")
    description = models.TextField(default=None, blank=True, null=True)
    rich_description = RichTextField(default="", blank=True, null=True)
    tags = models.ManyToManyField("Tag", default=None, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0)

    # Videos are ordered in descending order by the date they were taken. (newest to oldest)
    class Meta:
        ordering = ["-date_shot"]

    def __str__(self):
        return f"{self.name}, taken on {self.date_shot}"

    def delete(self):
        self.poster.delete()
        super().delete()

    def get_cname(self):
        return self.__class__.__name__

    def get_tags(self):
        return "\n".join([p.name for p in self.tags.all()])

    def get_absolute_url(self):
        return reverse("recent_shot", args=["external", self.id])


class Album(models.Model):
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Date added")
    name = models.CharField(max_length=200, unique=True)
    videos = models.ManyToManyField("Video", default=None, blank=True)
    external_videos = models.ManyToManyField("ExternalVideo", default=None, blank=True)
    description = models.TextField(default=None, blank=True, null=True)
    poster = models.FileField(upload_to="poster/%Y/%m/")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def delete(self):
        self.poster.delete()
        super().delete()

    def get_absolute_url(self):
        return reverse("album_view", args=[self.id])


class Tag(models.Model):
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Date added")
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=200, unique=True)
    label = models.CharField(max_length=50, unique=True)
    html_id = models.CharField(max_length=20, unique=False, verbose_name="HTML id")
    lat = models.DecimalField(max_digits=9, decimal_places=6, default=0)
    lon = models.DecimalField(max_digits=9, decimal_places=6, default=0)

    def __str__(self):
        return self.name
