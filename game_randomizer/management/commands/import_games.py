import json

from django.core.management.base import BaseCommand

from game_randomizer.models import Bundle, Game


class Command(BaseCommand):
    help = "Import games from a JSON file produced by export_games"

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="Path to the JSON export file")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report what would be imported without writing",
        )

    def handle(self, *args, **options):
        file_path = options["file"]
        dry_run = options["dry_run"]

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        if "bundles" not in data or "games" not in data:
            self.stderr.write(
                self.style.ERROR(
                    "Invalid file format: missing 'bundles' or 'games' key."
                )
            )
            return

        # Process bundles
        bundles_created = 0
        bundles_existing = 0
        bundle_map = {}  # url -> Bundle instance (for M2M linking)

        for b in data["bundles"]:
            if dry_run:
                exists = Bundle.objects.filter(url=b["url"]).exists()
                if exists:
                    bundles_existing += 1
                else:
                    bundles_created += 1
            else:
                bundle, created = Bundle.objects.get_or_create(
                    url=b["url"],
                    defaults={
                        "name": b["name"],
                        "expected_item_count": b.get("expected_item_count"),
                    },
                )
                bundle_map[b["url"]] = bundle
                if created:
                    bundles_created += 1
                else:
                    bundles_existing += 1

        # Process games
        games_created = 0
        games_existing = 0

        for g in data["games"]:
            if dry_run:
                exists = Game.objects.filter(
                    itch_game_id=g["itch_game_id"]
                ).exists()
                if exists:
                    games_existing += 1
                else:
                    games_created += 1
            else:
                game, created = Game.objects.get_or_create(
                    itch_game_id=g["itch_game_id"],
                    defaults={
                        "title": g["title"],
                        "developer": g["developer"],
                        "developer_url": g["developer_url"],
                        "description": g.get("description", ""),
                        "category_tag": g.get("category_tag", ""),
                        "image_url": g.get("image_url", ""),
                        "game_url": g["game_url"],
                        "platforms": g.get("platforms", []),
                    },
                )
                # Link bundles via URLs
                for bundle_url in g.get("bundle_urls", []):
                    bundle = bundle_map.get(bundle_url)
                    if bundle:
                        game.bundles.add(bundle)

                if created:
                    games_created += 1
                else:
                    games_existing += 1

        # Summary
        self.stdout.write("")
        prefix = "=== Dry Run Summary ===" if dry_run else "=== Import Summary ==="
        self.stdout.write(prefix)
        self.stdout.write(f"Bundles created:  {bundles_created}")
        self.stdout.write(f"Bundles existing: {bundles_existing}")
        verb = "Would create" if dry_run else "Games created"
        self.stdout.write(f"{verb}:  {games_created}")
        verb2 = "Already in DB" if dry_run else "Games existing"
        self.stdout.write(f"{verb2}:    {games_existing}")
