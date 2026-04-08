import os
import re
import time
from datetime import datetime

from django.core.management.base import BaseCommand

from game_randomizer.models import Bundle, Game


class Command(BaseCommand):
    help = "Scrape games from an itch.io bundle page using Playwright"

    def add_arguments(self, parser):
        parser.add_argument("bundle_url", type=str, help="The itch.io bundle page URL")
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Only scrape the first N games (for testing)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and print games but don't write to the database",
        )
        parser.add_argument(
            "--no-headless",
            action="store_true",
            help="Launch the browser visibly so you can watch Playwright scrape",
        )

    def handle(self, *args, **options):
        from playwright.sync_api import sync_playwright

        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

        bundle_url = options["bundle_url"]
        limit = options["limit"]
        dry_run = options["dry_run"]
        headless = not options["no_headless"]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless, args=["--start-maximized"])
            page = browser.new_page(no_viewport=True)

            try:
                self._scrape(page, bundle_url, limit, dry_run)
            finally:
                browser.close()

    def _scrape(self, page, bundle_url, limit, dry_run):
        self._start_time = time.monotonic()

        page.goto(bundle_url, wait_until="domcontentloaded")

        # Extract bundle info
        bundle_name = self._get_text(page, "h1.promotion_title") or "Unknown Bundle"
        expected_count = self._parse_expected_count(page)

        self._log(
            f'Bundle: "{bundle_name}" \u2014 expects {expected_count:,} items.'
            if expected_count
            else f'Bundle: "{bundle_name}" \u2014 expected item count not found.'
        )

        # Create or get bundle
        bundle = None
        if not dry_run:
            bundle, _ = Bundle.objects.get_or_create(
                url=bundle_url,
                defaults={
                    "name": bundle_name,
                    "expected_item_count": expected_count,
                },
            )

        # Scroll to load all games
        self._scroll_and_collect(page, limit)

        # Extract all game data in one browser call
        self._log("Extracting game data from page...")
        raw_games = self._extract_all_games(page, limit)
        # Re-encode '#' in image URLs — the browser decodes %23 to # when
        # reading from the DOM and there's no way to prevent it.
        for g in raw_games:
            if g.get("image_url"):
                g["image_url"] = g["image_url"].replace("#", "%23")
        self._log(f"Extracted {len(raw_games):,} raw game entries.")

        # Validate and filter
        games_data = []
        skipped = 0
        for i, data in enumerate(raw_games):
            if not data.get("itch_game_id"):
                self._log_err(
                    f"[WARNING] Skipped game cell \u2014 could not parse "
                    f"data-game_id (position {i} in grid)"
                )
                skipped += 1
                continue
            if not data.get("title") or not data.get("game_url"):
                self._log_err(
                    f"[WARNING] Skipped game cell \u2014 missing title or game_url "
                    f"(data-game_id: {data.get('itch_game_id')})"
                )
                skipped += 1
                continue
            games_data.append(data)

        # Process results
        new_count = 0
        existing_count = 0

        for data in games_data:
            if dry_run:
                self._log(
                    f'[DRY RUN] Would create: "{data["title"]}" by '
                    f'{data["developer"]} (ID: {data["itch_game_id"]})'
                )
                # Check if already in DB for accurate dry-run reporting
                if Game.objects.filter(itch_game_id=data["itch_game_id"]).exists():
                    existing_count += 1
                else:
                    new_count += 1
            else:
                game, created = Game.objects.get_or_create(
                    itch_game_id=data["itch_game_id"],
                    defaults={
                        "title": data["title"],
                        "developer": data["developer"],
                        "developer_url": data["developer_url"],
                        "description": data["description"],
                        "category_tag": data["category_tag"],
                        "image_url": data["image_url"],
                        "game_url": data["game_url"],
                        "platforms": data["platforms"],
                    },
                )
                game.bundles.add(bundle)
                if created:
                    new_count += 1
                else:
                    existing_count += 1

        # Print summary
        self._print_summary(
            bundle_name=bundle_name,
            expected_count=expected_count,
            total_scraped=len(games_data),
            new_count=new_count,
            existing_count=existing_count,
            skipped=skipped,
            dry_run=dry_run,
            limit=limit,
        )

    def _scroll_and_collect(self, page, limit):
        # Wait for the game grid to load before scrolling
        try:
            page.wait_for_selector("div.game_column .game_cell", timeout=30000)
        except Exception:
            self._log_err(
                "[WARNING] Timed out waiting for game grid to load."
            )
            return []

        previous_count = 0
        scroll_pass = 0

        while True:
            game_cells = page.query_selector_all("div.game_column .game_cell")
            current_count = len(game_cells)
            scroll_pass += 1

            self._log(
                f"Scroll pass {scroll_pass}: {current_count:,} games loaded..."
            )

            if limit and current_count >= limit:
                break
            if current_count == previous_count:
                self._log(
                    f"No new games after scroll \u2014 grid complete."
                )
                break

            previous_count = current_count
            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

        return

    def _extract_all_games(self, page, limit):
        js = """
        (limit) => {
            let cells = document.querySelectorAll('div.game_column .game_cell');
            if (limit) cells = Array.from(cells).slice(0, limit);
            else cells = Array.from(cells);

            return cells.map(cell => {
                const gameId = cell.getAttribute('data-game_id');
                const titleEl = cell.querySelector('a.title');
                const userEl = cell.querySelector('.user_link');
                const descEl = cell.querySelector('.sub.short_text, .short_text');
                const tagEl = cell.querySelector('.cell_tags a');
                const imgEl = cell.querySelector('img');

                const platforms = [];
                cell.querySelectorAll('[class*="icon-"]').forEach(el => {
                    el.className.split(/\\s+/).forEach(cls => {
                        if (cls.startsWith('icon-')) {
                            const p = cls.substring(5);
                            if (p && !platforms.includes(p)) platforms.push(p);
                        }
                    });
                });

                return {
                    itch_game_id: gameId ? parseInt(gameId, 10) || null : null,
                    title: titleEl ? titleEl.innerText.trim() : '',
                    game_url: titleEl ? titleEl.getAttribute('href') || '' : '',
                    developer: userEl ? userEl.innerText.trim() : '',
                    developer_url: userEl ? userEl.getAttribute('href') || '' : '',
                    description: descEl ? descEl.innerText.trim() : '',
                    category_tag: tagEl ? tagEl.innerText.trim() : '',
                    image_url: imgEl ? imgEl.getAttribute('src') || '' : '',
                    platforms: platforms,
                };
            });
        }
        """
        return page.evaluate(js, limit)

    def _log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.stdout.write(f"[{timestamp}] {message}")

    def _log_err(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.stderr.write(f"[{timestamp}] {message}")

    def _parse_expected_count(self, page):
        text = self._get_text(page, ".bundle_rate")
        if not text:
            return None
        match = re.search(r"([\d,]+)\s+items", text)
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    def _get_text(self, parent, selector):
        el = parent.query_selector(selector)
        if el:
            return el.inner_text().strip()
        return None

    def _print_summary(
        self,
        bundle_name,
        expected_count,
        total_scraped,
        new_count,
        existing_count,
        skipped,
        dry_run,
        limit,
    ):
        elapsed = time.monotonic() - self._start_time
        minutes, seconds = divmod(int(elapsed), 60)

        self._log("")
        if dry_run:
            self._log("=== Dry Run Summary ===")
            self._log(f'Bundle:           "{bundle_name}"')
            if expected_count:
                self._log(f"Expected items:   {expected_count:,}")
            limited_note = f" (limited by --limit {limit})" if limit else ""
            self._log(f"Games parsed:     {total_scraped:,}{limited_note}")
            self._log(f"Would create:     {new_count:,}")
            self._log(f"Already in DB:    {existing_count:,}")
            self._log(f"Skipped (errors): {skipped:,}")
        else:
            self._log("=== Scrape Summary ===")
            self._log(f'Bundle:           "{bundle_name}"')
            if expected_count:
                self._log(f"Expected items:   {expected_count:,}")
            self._log(f"Games scraped:    {total_scraped:,}")
            self._log(f"New games added:  {new_count:,}")
            self._log(f"Already existed:  {existing_count:,}")
            self._log(f"Skipped (errors): {skipped:,}")

            if expected_count and not limit:
                if total_scraped == expected_count:
                    self._log(
                        "Status:           \u2713 OK \u2014 scraped count matches expected."
                    )
                else:
                    diff = expected_count - total_scraped
                    self._log(
                        f"Status:           \u26a0 WARNING \u2014 expected "
                        f"{expected_count:,} but only scraped "
                        f"{total_scraped:,} ({diff:,} missing)."
                    )
                    self._log(
                        "                  Possible causes: scroll didn't reach "
                        "bottom, page load timeout,"
                    )
                    self._log(
                        "                  or items failed to parse. Re-run with "
                        "--limit to test, or check"
                    )
                    self._log(
                        "                  warnings above for skipped games."
                    )

        self._log(f"Time taken:       {minutes}m {seconds}s")
