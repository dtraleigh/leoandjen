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
python manage.py scrape_bundle <bundle_url> [--limit N] [--dry-run] [--no-headless]
```

**Arguments:**
| Arg/Flag       | Description                                                        |
|----------------|--------------------------------------------------------------------|
| `bundle_url`   | Required. The itch.io bundle page URL.                             |
| `--limit N`    | Optional. Only scrape the first N games (for testing).             |
| `--dry-run`    | Optional. Parse and print games but don't write to the database.   |
| `--no-headless`| Optional. Launch the browser visibly so you can watch Playwright scrape. Headless by default. |

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
7. For each game cell, extract:
   - `data-game_id` → `itch_game_id`
   - `.title` text and href → `title`, `game_url`
   - `.user_link` text and href → `developer`, `developer_url`
   - `.sub.short_text` text → `description`
   - `.sub.cell_tags a` text → `category_tag` (if present; not all games have one)
   - `img` src → `image_url`
   - Platform icons (`.icon-windows8`, `.icon-apple`, `.icon-tux`, etc.) → `platforms` list
   - **Per-game error handling:** If any required field (`itch_game_id`, `title`, `game_url`) is missing or unparseable, log a warning with as much identifying info as possible and skip the game:
     ```
     [WARNING] Skipped game cell — missing title (data-game_id: 366363)
     [WARNING] Skipped game cell — could not parse data-game_id (position 247 in grid)
     ```
8. **Deduplication:** Use `itch_game_id` to `get_or_create`. If the game already exists, just add the current bundle to its M2M `bundles` field.
9. **Final summary with verification:**
   ```
   === Scrape Summary ===
   Bundle:           "No ICE in Minnesota"
   Expected items:   1,439
   Games scraped:    1,439
   New games added:  1,204
   Already existed:  235
   Skipped (errors): 0
   Status:           ✓ OK — scraped count matches expected.
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
- [ ] Models with migrations
- [ ] Admin registrations with search/filter
- [ ] Working `scrape_bundle` command with `--limit`, `--dry-run`, and `--no-headless`
- [ ] `export_games` management command
- [ ] `import_games` management command with `--dry-run`
- [ ] Requirements: add `playwright` to `requirements_local.txt` only (not `requirements_server.txt`). Run `playwright install chromium` locally after install.

---

## Phase 2 — The Randomizer Page

### Goals
- Build the main randomizer view and template
- Implement a fun, animated game-selection experience
- All views protected with `@login_required`

### User Flow
1. User visits the randomizer page (`/randomizer/`).
2. User selects how many games to pick: **1**, **2**, or **3** (toggle buttons or selector).
3. Optionally, user can toggle **"Unplayed only"** to exclude games that already have a rating.
4. User clicks **"Spin!"** (or equivalent).
5. A slot-machine-style animation plays:
   - Game thumbnails scroll rapidly through a visible "reel."
   - The reel(s) decelerate and land on the selected game(s).
   - If picking multiple games, show multiple reels side by side.
6. The selected game(s) are revealed with their title, image, developer, and description.
7. Each result card links to the game's detail/review page.

### Technical Approach
- **Backend:** A simple Django view serves the page. An API endpoint (`/randomizer/api/spin/`) accepts a `count` (1–3) and `unplayed_only` (bool), returns that many random `Game` records as JSON.
- **Frontend:** Vanilla JS + CSS animations for the slot machine effect. The page pre-fetches a pool of game images/titles on load to populate the reel animation, then swaps in the real results at the end.
- **Randomization:** Use `Game.objects.order_by('?')[:count]` or `random.sample()` on IDs for better performance on large sets.

### Deliverables
- [ ] Randomizer page view + template
- [ ] `/api/spin/` JSON endpoint
- [ ] Slot machine animation (CSS + JS)
- [ ] Selection UI for 1/2/3 games
- [ ] "Unplayed only" filter toggle
- [ ] Responsive layout

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
- [ ] Game detail view + template
- [ ] Star rating widget (interactive, 3-star)
- [ ] Notes textarea with save functionality
- [ ] Visual indicators for rated vs. unrated games
- [ ] Link to itch.io game page

---

## Phase 4 — Browse & Polish

### Goals
- A way to browse all games in the database
- Filtering, search, and overall UX polish

### Features
- **Game list page** (`/randomizer/games/`):
  - Grid view showing game thumbnails, titles, and rating status
  - Search by title or developer
  - Filter by: bundle, rating status (unrated / 1 / 2 / 3 stars), platform
  - Sort by: title, date added, rating
  - Pagination or infinite scroll
- **Dashboard stats** (optional, on the main randomizer page):
  - Total games in DB
  - Games reviewed vs. unreviewed
  - Rating distribution
- **UX polish:**
  - Consistent styling across all pages
  - Mobile-friendly responsive design
  - Loading states and error handling

### Deliverables
- [ ] Game list view with search and filters
- [ ] Pagination
- [ ] Dashboard stats widget
- [ ] Responsive styling pass
- [ ] Error/empty states

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
