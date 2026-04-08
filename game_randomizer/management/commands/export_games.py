import json
import os

from django.core.management.base import BaseCommand
from django.utils import timezone

from game_randomizer.models import Bundle, Game


class Command(BaseCommand):
    help = "Export all Bundle and Game data to a portable JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="game_randomizer_export.json",
            help="Output file path (default: game_randomizer_export.json)",
        )

    def handle(self, *args, **options):
        output_path = options["output"]

        bundles = Bundle.objects.all()
        games = Game.objects.prefetch_related("bundles").all()

        data = {
            "exported_at": timezone.now().isoformat(),
            "bundles": [
                {
                    "name": b.name,
                    "url": b.url,
                    "expected_item_count": b.expected_item_count,
                }
                for b in bundles
            ],
            "games": [
                {
                    "itch_game_id": g.itch_game_id,
                    "title": g.title,
                    "developer": g.developer,
                    "developer_url": g.developer_url,
                    "description": g.description,
                    "category_tag": g.category_tag,
                    "image_url": g.image_url,
                    "game_url": g.game_url,
                    "platforms": g.platforms,
                    "bundle_urls": [b.url for b in g.bundles.all()],
                }
                for g in games
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        file_size = os.path.getsize(output_path)
        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {len(data['bundles'])} bundle(s) and "
                f"{len(data['games'])} game(s) to {output_path} "
                f"({file_size:,} bytes)"
            )
        )
