from django.contrib import admin

from game_randomizer.models import Bundle, Game, GameReview


class BundleAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "expected_item_count", "created_at")
    search_fields = ("name",)


class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "developer", "itch_game_id", "category_tag", "created_at")
    search_fields = ("title", "developer")
    list_filter = ("bundles", "category_tag")
    filter_horizontal = ("bundles",)


class GameReviewAdmin(admin.ModelAdmin):
    list_display = ("game", "rating", "reviewed_at")
    search_fields = ("game__title",)
    list_filter = ("rating",)


admin.site.register(Bundle, BundleAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(GameReview, GameReviewAdmin)
