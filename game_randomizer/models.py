from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Bundle(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    expected_item_count = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}"


class Game(models.Model):
    itch_game_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    developer = models.CharField(max_length=255)
    developer_url = models.URLField(max_length=500)
    description = models.TextField(blank=True)
    category_tag = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    game_url = models.URLField(max_length=500)
    platforms = models.JSONField(default=list)
    bundles = models.ManyToManyField(Bundle, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} by {self.developer}"


class GameReview(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name="review")
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
    )
    notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-reviewed_at"]

    def __str__(self):
        return f"Review for {self.game.title}"
