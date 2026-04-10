# Game Randomizer — Django App Spec

## Overview

A Django app that scrapes game data from itch.io bundles, stores it locally, and presents a fun slot-machine-style randomizer to pick games to play. Users can then review and rate the games they've tried. The app is protected behind Django's built-in authentication — any logged-in user can access it, but it is not publicly visible.

---

## Data Models

### Bundle

Tracks each itch.io bundle so we know where games came from.

| Field        | Type              | Notes                                    |
|--------------|-------------------|------------------------------------------|
| `id`         | AutoField (PK)    |                                          |
| `name`       | CharField(255)    | From `h1.promotion_title` on the bundle page |
| `url`        | URLField (unique) | The bundle page URL                      |
| `expected_item_count` | IntegerField (null) | Parsed from `.bundle_rate` (e.g. 1439) |
| `created_at` | DateTimeField     | Auto-set on creation                     |

### Game

Core model for each game item.

| Field          | Type                | Notes                                                  |
|----------------|---------------------|--------------------------------------------------------|
| `id`           | AutoField (PK)      |                                                        |
| `itch_game_id` | IntegerField(unique)| From `data-game_id` attribute; used for deduplication  |
| `title`        | CharField(255)      |                                                        |
| `developer`    | CharField(255)      | From `.user_link` text                                 |
| `developer_url`| URLField            | From `.user_link` href                                 |
| `description`  | TextField (blank)   | From `.sub.short_text`                                 |
| `category_tag` | CharField (blank)   | From `.sub.cell_tags a` text (e.g. "#Physical games") |
| `image_url`    | URLField (blank)    | Thumbnail URL from `img` src                           |
| `game_url`     | URLField            | From `.title` href                                     |
| `platforms`    | JSONField (default=list) | e.g. `["windows", "macos", "linux"]`              |
| `bundles`      | M2M → Bundle        | Which bundles this game appeared in                    |
| `created_at`   | DateTimeField       | Auto-set on creation                                   |
| `updated_at`   | DateTimeField       | Auto-set on save                                       |

### GameReview

User notes and rating for a game.

| Field      | Type                 | Notes                                          |
|------------|----------------------|-------------------------------------------------|
| `id`       | AutoField (PK)       |                                                 |
| `game`     | OneToOneField → Game | One review per game                             |
| `rating`   | IntegerField (null)  | `None` = unrated, `1`, `2`, or `3` stars        |
| `notes`    | TextField (blank)    | Free-form text                                  |
| `reviewed_at` | DateTimeField     | Auto-set on save                                |

> **Note:** Reviews are global (not tied to a specific user). The app is single-user in practice; Django auth is used only as a gatekeeper to keep the app private.

---

## Phase 1 — Models, Admin, and Management Command

### Goals
- Define and migrate all models (`Bundle`, `Game`, `GameReview`)
- Register models in Django admin for manual inspection
- Build the `scrape_bundle` management command

### Management Command: `scrape_bundle`

**Usage:**
```bash
python manage.py scrape_bundle <bundle_url> [--limit N] [--dry-run] [--no-headless] [--update]
```

**Arguments:**
| Arg/Flag       | Description                                                        |
|----------------|--------------------------------------------------------------------|
| `bundle_url`   | Required. The itch.io bundle page URL.                             |
| `--limit N`    | Optional. Only scrape the first N games (for testing).             |
| `--dry-run`    | Optional. Parse and print games but don't write to the database.   |
| `--no-headless`| Optional. Launch the browser visibly so you can watch Playwright scrape. Headless by default. |
| `--update`     | Optional. Update existing games with freshly scraped data (e.g. to backfill missing images). |

**Behavior:**
1. Launch Playwright browser (Chromium). Headless by default; pass `--no-headless` to open a visible browser window for debugging.
2. Navigate to the bundle URL.
3. Scrape the bundle title from `h1.promotion_title` → create or get the `Bundle` record.
4. Scrape the **expected item count** from `.bundle_rate` (parse the number from text like "Buy 1,439 items for $10"). Log it immediately:
   ```
   Bundle: "No ICE in Minnesota" — expects 1,439 items.
   ```
5. Locate the game grid container (`div.game_column`).
6. **Scroll loop:** scrape all visible `.game_cell` elements within `div.game_column`, scroll down, wait for new content, repeat until either:
   - The bottom of the grid is reached (no new games loaded), or
   - The `--limit` count is met.
   - **Progress output** during scrolling:
     ```
     Scroll pass 1: 30 games loaded...
     Scroll pass 2: 60 games loaded...
     ...
     Scroll pass 48: 1,439 games loaded. No new games after scroll — grid complete.
     ```
6b. **Image loading scroll:** After all game cells are loaded, scroll back through the page in viewport-sized steps to trigger lazy loading on all images. Without this, images below the initial viewport have empty `src` attributes.
7. For each game cell, extract (via a single `page.evaluate()` JS call for performance):
   - `data-game_id` → `itch_game_id`
   - `a.title` text and href → `title`, `game_url`
   - `.user_link` text and href → `developer`, `developer_url`
   - `.sub.short_text, .short_text` text → `description`
   - `.cell_tags a` text → `category_tag` (if present; not all games have one)
   - `img` src → `image_url` (note: browser decodes `%23` to `#` in URLs; re-encode after extraction)
   - Platform icons (`[class*="icon-"]`, dynamically collected) → `platforms` list
   - **Per-game error handling:** If any required field (`itch_game_id`, `title`, `game_url`) is missing or unparseable, log a warning with as much identifying info as possible and skip the game:
     ```
     [WARNING] Skipped game cell — missing title (data-game_id: 366363)
     [WARNING] Skipped game cell — could not parse data-game_id (position 247 in grid)
     ```
8. **Deduplication:** Use `itch_game_id` to `get_or_create`. If the game already exists, just add the current bundle to its M2M `bundles` field. With `--update`, existing games are compared field-by-field and saved if any field changed.
9. **Final summary with verification:**
   ```
   === Scrape Summary ===
   Bundle:           "No ICE in Minnesota"
   Expected items:   1,439
   Games scraped:    1,439
   New games added:  1,204
   Updated:          50
   Already existed:  185
   Skipped (errors): 0
   Missing images:   7

   Games missing images:
     - "Some Game" by Developer (ID: 12345)
     ...

   Status:           ✓ OK — scraped count matches expected.
   Time taken:       3m 45s
   ```
   If the counts don't match:
   ```
   Status:           ⚠ WARNING — expected 1,439 but only scraped 1,286 (153 missing).
                     Possible causes: scroll didn't reach bottom, page load timeout,
                     or items failed to parse. Re-run with --limit to test, or check
                     warnings above for skipped games.
   ```

**Dry-run output example:**
```
Bundle: "No ICE in Minnesota" — expects 1,439 items.
[DRY RUN] Would create: "Baba Is You" by Hempuli (ID: 366363)
[DRY RUN] Would create: "Celeste" by Maddy Thorson (ID: 140890)
...

=== Dry Run Summary ===
Expected items:   1,439
Games parsed:     10 (limited by --limit 10)
Would create:     10
Already in DB:    0
Skipped (errors): 0
```

### Management Command: `export_games`

Since `scrape_bundle` requires Playwright and Chromium (which may not be available on shared hosting), this command exports all scraped data to a portable JSON file that can be transferred to the server.

**Usage:**
```bash
python manage.py export_games [--output FILE]
```

**Arguments:**
| Arg/Flag       | Description                                                        |
|----------------|--------------------------------------------------------------------|
| `--output FILE`| Optional. Output file path. Defaults to `game_randomizer_export.json`. |

**Behavior:**
1. Serializes all `Bundle` and `Game` records (with their M2M relationships) to a JSON file.
2. Does **not** export `GameReview` data (reviews live on the server only).
3. Prints a summary: bundles exported, games exported, file size.

**Output format:**
```json
{
  "exported_at": "2026-04-05T12:00:00Z",
  "bundles": [
    {"name": "No ICE in Minnesota", "url": "https://...", "expected_item_count": 1439}
  ],
  "games": [
    {
      "itch_game_id": 366363,
      "title": "Baba Is You",
      "developer": "Hempuli",
      "developer_url": "https://hempuli.itch.io",
      "description": "A puzzle game where you change the rules...",
      "category_tag": "",
      "image_url": "https://img.itch.zone/...",
      "game_url": "https://hempuli.itch.io/baba",
      "platforms": ["windows", "macos", "linux"],
      "bundle_urls": ["https://itch.io/b/3484/no-ice-in-minnesota"]
    }
  ]
}
```

### Management Command: `import_games`

Imports a JSON file produced by `export_games` into the database on the server.

**Usage:**
```bash
python manage.py import_games <file> [--dry-run]
```

**Arguments:**
| Arg/Flag   | Description                                                        |
|------------|--------------------------------------------------------------------|
| `file`     | Required. Path to the JSON export file.                            |
| `--dry-run`| Optional. Parse and report what would be imported without writing.  |

**Behavior:**
1. Reads the JSON file and validates its structure.
2. Creates or gets `Bundle` records.
3. For each game, uses `itch_game_id` to `get_or_create`, same as the scraper — existing games just get their bundle M2M updated.
4. Prints a summary: games created, games already existing, bundles created.

### Intended Workflow

```
Local machine                          Shared host (server)
─────────────                          ────────────────────
1. scrape_bundle <url>          →
2. export_games --output data.json
3. scp data.json server:~/      →      4. import_games data.json
```

### Phase 1 Deliverables
- [x] Models with migrations
- [x] Admin registrations with search/filter
- [x] Working `scrape_bundle` command with `--limit`, `--dry-run`, and `--no-headless`
- [x] `export_games` management command
- [x] `import_games` management command with `--dry-run`
- [x] Requirements: add `playwright` to `requirements_local.txt` only (not `requirements_server.txt`). Run `playwright install chromium` locally after install.

### Phase 1 Implementation Notes
- Game data extraction uses a single `page.evaluate()` JS call for performance (avoids per-cell Playwright IPC round-trips).
- `DJANGO_ALLOW_ASYNC_UNSAFE` is set in the scrape command to work around Playwright's event loop conflicting with Django's async safety check.
- Browser launches maximized (`--start-maximized` + `no_viewport=True`) for reliable rendering.
- Scraper waits for `.game_cell` selector (30s timeout) before starting scroll loop to handle lazy-loaded pages.
- All output lines are timestamped; final summary includes total elapsed time.

---

## Phase 2 — The Randomizer Page

### Goals
- Build the main randomizer view and template
- Implement a fun, animated game-selection experience
- All views protected with `@login_required`

### User Flow
1. User visits the randomizer page (`/randomizer/`).
2. A **dashboard panel** at the top shows total games, reviewed count, unplayed count, and 1/2/3-star rating distribution.
3. The page always picks **3** games (no count selector).
4. Optionally, user can toggle **"Unplayed only"** to exclude games that already have a rating.
5. Optionally, user can click **category pills** to exclude one or more categories from the random pool. All categories are included by default; clicking a pill toggles it to an excluded (dashed border, strikethrough) state.
6. User clicks **"Spin!"**.
7. A slot-machine-style animation plays:
   - Three large side-by-side reels scroll rapidly through game thumbnails.
   - The reels decelerate in a staggered cascade and land on the selected games.
8. The selected games are revealed in a distinct **"Your Picks"** results panel (purple-bordered, gradient background) below the reels, with each card aligned beneath its corresponding reel.
9. Each result card links to the game's detail/review page and to itch.io.

### Technical Approach
- **Backend:** A simple Django view serves the page. An API endpoint (`/randomizer/api/spin/`) accepts a `count` (1–3), `unplayed_only` (bool), and zero or more `exclude_category` query params, returns that many random `Game` records as JSON.
- **Frontend:** Vanilla JS + CSS animations for the slot machine effect. The page pre-fetches a pool of game images/titles on load to populate the reel animation, then swaps in the real results at the end.
- **Randomization:** Use `random.sample()` on a filtered ID list (avoids `ORDER BY RANDOM()` on large sets).

### Deliverables
- [x] Randomizer page view + template
- [x] `/api/spin/` JSON endpoint
- [x] Slot machine animation (CSS + JS)
- [x] Fixed 3-reel layout
- [x] "Unplayed only" filter toggle
- [x] Category exclusion pills
- [x] Dashboard stats panel
- [x] Distinct "Your Picks" results section
- [x] Responsive layout

### Phase 2 Implementation Notes
- Spin endpoint uses GET (idempotent read, no CSRF needed). Randomization via `random.sample()` on ID list.
- "Unplayed" filter: `Q(review__isnull=True) | Q(review__rating__isnull=True)`.
- Category exclusion: API reads `request.GET.getlist("exclude_category")` and applies `.exclude(category_tag__in=excluded)`.
- Filler pool: 20 random games with images pre-fetched on page load, embedded as JSON in template context.
- Slot machine animation is three-phase per reel: accelerate (3s), cruise at constant speed (2s), decelerate with cubic ease-out (remaining time). Reel 1 = 10s, Reel 2 = 15s, Reel 3 = 20s. Strip wraps continuously to keep tiles visible.
- Layout uses a fluid container with three large flex reels that share most of the page width (`max-width: 480px` per reel on desktop, scaling down via CSS breakpoints at 992px and 768px). Reel count is hard-coded to 3 — no count selector.
- Tile height is read dynamically from rendered DOM at spin time so the animation works correctly across all responsive breakpoints. Reels rebuild on window resize (debounced 200ms) to keep tile geometry in sync.
- Unplayed toggle and category pills are disabled during spin.
- Custom-styled pill toggle replaces Bootstrap's `custom-switch` for the unplayed control — larger 56×30 track with glow on active.
- Category pills sit on a single non-wrapping row. Active pills are solid purple; excluded pills use a transparent background with dashed dark-red border, strikethrough text, and reduced opacity for clear visual contrast.
- Page layout below the heading: dashboard stats (centered), Spin button, unplayed toggle, category pills, reels, results section.
- Games with no image use a placeholder SVG (`static/img/no-image.svg`); also used as `onerror` fallback.
- Results section is wrapped in a `<section>` with its own gradient background, purple border, and "YOUR PICKS" heading. Result cards use the same flex layout as the reels (`flex: 1 1 0`, `max-width: 480px`) so each card aligns vertically under its reel.
- Result cards link to the game detail page and to itch.io.
- Dark theme with purple accent (#6c63ff) matching the reel styling.
- Bootstrap 4.6.2 loaded from data app's static files (no duplication).

---

## Phase 3 — Game Detail & Review Page

### Goals
- Individual game pages for viewing details and submitting reviews
- Star rating widget and notes field

### User Flow
1. User clicks a game (from randomizer results, or from a browse view).
2. Game detail page (`/randomizer/game/<id>/`) shows:
   - Game image (large)
   - Title, developer (linked to itch.io profile), description
   - Category tag and platforms (if available)
   - Link to the game on itch.io
   - Bundle(s) this game came from
3. Below the details, a **review section**:
   - **3-star rating widget:** clickable stars. Clicking a star sets that rating; clicking the active star again clears it back to "unrated."
   - **Notes:** a textarea for free-form notes.
   - **Save** button to persist the review.
4. If a review already exists, it loads pre-filled.

### Technical Approach
- **Backend:** Standard Django detail view. Review save can be a form POST or a small AJAX endpoint for a smoother experience.
- **Frontend:** Interactive star rating using CSS + minimal JS (no heavy libraries). Stars visually highlight on hover and lock on click.

### Deliverables
- [x] Game detail view + template
- [x] Star rating widget (interactive, 3-star)
- [x] Notes textarea with save functionality
- [x] Visual indicators for rated vs. unrated games
- [x] Link to itch.io game page

### Phase 3 Implementation Notes
- Three-column layout: image (left), info (middle), review form (right) — stacks vertically on small screens.
- Star widget uses click handlers to set rating; clicking the active star clears it.
- Save uses AJAX POST to `/randomizer/game/<id>/review/` with CSRF token; status indicator fades in/out.

---

## Phase 4 — Browse & Polish

### Goals
- A way to browse all games in the database
- Filtering, search, and overall UX polish

### Features
- **Game list page** (`/randomizer/games/`):
  - Sortable table with columns: #, Title, Developer (linked), Category, Platform (icons), Rating
  - Search by title or developer
  - Filter by: bundle, category, rating status (unrated / 1 / 2 / 3 stars), platform
  - All columns sortable by clicking the header
- **Dashboard stats** on the main randomizer page:
  - Total games in DB
  - Games reviewed vs. unreviewed
  - Rating distribution
- **UX polish:**
  - Consistent styling across all pages
  - Mobile-friendly responsive design
  - Loading states and error handling

### Deliverables
- [x] Game list view with search and filters
- [x] Sortable table columns
- [x] Category dropdown filter
- [x] Platform icons (Windows / macOS / Linux / Android)
- [x] Dashboard stats widget on randomizer page
- [x] Responsive styling pass
- [x] Error/empty states

### Phase 4 Implementation Notes
- Game list page is a sortable table with columns: #, Title, Developer, Category, Platform, Rating.
- Title links to the game detail page; Developer links to the developer's itch.io profile.
- Platform column renders SVG icons for `windows`/`windows8`, `apple`/`osx`/`macos`, `tux`/`linux`, and `android`. Unknown platform values fall back to displaying the raw string. Games with no platform data show a hyphen.
- Rating column shows three gold/dark stars or "No Rating".
- All columns sort client-side; rating sorts by numeric value (using `data-rating` attribute on the row), the rest sort alphabetically. The `#` column re-numbers visible rows after each sort.
- Search filters by title or developer (case-insensitive substring).
- Filter dropdowns: **bundle**, **category**, **rating** (any/unrated/1/2/3), **platform**. A Clear button resets all filters.
- All filtering/sorting happens client-side over the full row set — no pagination needed at current scale (~1.5k rows).
- Distinct category list for the dropdown is built with `.order_by().values_list().distinct()` — the explicit `.order_by()` is required to clear `Game.Meta.ordering = ["title"]`, otherwise Django includes `title` in the SELECT and breaks the distinct.
- Empty state shows when filters return no rows; visible row count updates live ("Showing X of Y games").
- Dashboard stats on randomizer page show: total games, reviewed, unplayed, and 1/2/3-star rating distribution. Centered with `width: fit-content` + `margin: auto`.
- Top nav bar links to the Game List page. The "Game Randomizer" brand acts as the link back to the randomizer, so a separate Randomizer nav link is unnecessary.

---

## Phase Summary

| Phase | Focus                          | Key Output                          |
|-------|--------------------------------|-------------------------------------|
| 1     | Models + Scraping              | DB schema, admin, management command|
| 2     | Randomizer                     | Animated game picker page           |
| 3     | Game Detail & Reviews          | Detail pages, ratings, notes        |
| 4     | Browse & Polish                | Game list, search, filters, polish  |

---

## Tech Stack Notes

- **Django 5.1.x**
- **PostgreSQL** (already configured)
- **Bootstrap** (already used by other apps in the project) + vanilla JS for slot machine animation
- **Django auth** with `@login_required` on all views
- No external frontend build step required

### Requirements File Split

The project maintains two separate requirements files:

- **`requirements_local.txt`** — includes `playwright` (and its dependencies like `greenlet`) for running `scrape_bundle`. Playwright's C++ dependencies cannot compile on the shared host, so it must never be added to the server file.
- **`requirements_server.txt`** — everything needed to run the Django app in production. The `import_games` command has no special dependencies beyond Django itself. The `scrape_bundle` command is not intended to run on the server.
