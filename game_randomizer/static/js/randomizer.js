(function () {
    "use strict";

    const REEL_COUNT = 3;
    const TILES_IN_STRIP = 80;
    const BASE_DURATION = 10000;
    const STAGGER_MS = 5000;

    let spinning = false;

    const spinBtn = document.getElementById("spinBtn");
    const reelsContainer = document.getElementById("reelsContainer");
    const resultsContainer = document.getElementById("resultsContainer");
    const resultsSection = document.getElementById("resultsSection");

    // --- Reel building ---

    function createTile(game) {
        const tile = document.createElement("div");
        tile.className = "reel-tile";
        const img = document.createElement("img");
        img.src = game.image_url || PLACEHOLDER_IMG;
        img.alt = game.title;
        img.loading = "lazy";
        img.onerror = function () {
            this.src = PLACEHOLDER_IMG;
        };
        tile.appendChild(img);
        const label = document.createElement("div");
        label.className = "tile-title";
        label.textContent = game.title;
        tile.appendChild(label);
        return tile;
    }

    function buildReels() {
        reelsContainer.innerHTML = "";
        for (let i = 0; i < REEL_COUNT; i++) {
            const window_ = document.createElement("div");
            window_.className = "reel-window";

            const highlight = document.createElement("div");
            highlight.className = "reel-highlight";
            window_.appendChild(highlight);

            const strip = document.createElement("div");
            strip.className = "reel-strip";

            // Fill strip with shuffled filler tiles
            for (let t = 0; t < TILES_IN_STRIP; t++) {
                const game = FILLER_POOL[t % FILLER_POOL.length];
                strip.appendChild(createTile(game));
            }

            window_.appendChild(strip);
            reelsContainer.appendChild(window_);
        }
    }

    function shuffleArray(arr) {
        const a = arr.slice();
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    // --- Animation ---

    // Three-phase animation: accelerate (3s) -> constant speed (variable) -> decelerate (remaining)
    const ACCEL_DURATION = 3000;
    const CRUISE_DURATION = 2000;
    const MAX_SPEED = 5.0; // pixels per ms at full speed

    function animateReel(strip, targetOffset, duration, tileHeight) {
        return new Promise(function (resolve) {
            const startTime = performance.now();
            const stripHeight = TILES_IN_STRIP * tileHeight;

            // Phase timing: accel is fixed 3s, cruise is variable, decel gets the rest
            const decelDuration = duration - ACCEL_DURATION - CRUISE_DURATION;

            // Distance covered during acceleration (ease-in: 0 -> MAX_SPEED)
            // integral of MAX_SPEED * easeIn(t) over ACCEL_DURATION
            // with easeIn(t) = t^2, integral = 1/3, so distance = MAX_SPEED * ACCEL_DURATION / 3
            const accelDistance = MAX_SPEED * ACCEL_DURATION / 3;

            // Distance during cruise
            const cruiseDistance = MAX_SPEED * CRUISE_DURATION;

            // Position at start of decel phase (unwrapped)
            const decelStartPos = accelDistance + cruiseDistance;
            const decelStartWrapped = ((decelStartPos % stripHeight) + stripHeight) % stripHeight;

            // Figure out how far decel needs to travel to land on target
            let decelRemaining = targetOffset - decelStartWrapped;
            // Ensure we travel forward at least 2 full wraps for visual continuity
            while (decelRemaining < stripHeight * 2) decelRemaining += stripHeight;

            function easeOutCubic(t) {
                return 1 - Math.pow(1 - t, 3);
            }

            function frame(now) {
                const elapsed = now - startTime;
                let rawY;

                if (elapsed < ACCEL_DURATION) {
                    // Phase 1: Accelerate (ease in from 0 to max speed)
                    const t = elapsed / ACCEL_DURATION;
                    rawY = accelDistance * t * t * t;

                } else if (elapsed < ACCEL_DURATION + CRUISE_DURATION) {
                    // Phase 2: Constant max speed
                    const cruiseElapsed = elapsed - ACCEL_DURATION;
                    rawY = accelDistance + MAX_SPEED * cruiseElapsed;

                } else if (elapsed < duration) {
                    // Phase 3: Decelerate (ease out to target)
                    const decelElapsed = elapsed - ACCEL_DURATION - CRUISE_DURATION;
                    const t = decelElapsed / decelDuration;
                    const eased = easeOutCubic(t);
                    rawY = decelStartPos + decelRemaining * eased;

                } else {
                    rawY = decelStartPos + decelRemaining;
                }

                // Wrap within strip so tiles always stay visible
                const currentY = ((rawY % stripHeight) + stripHeight) % stripHeight;
                strip.style.transform = "translateY(" + (-currentY) + "px)";

                if (elapsed < duration) {
                    requestAnimationFrame(frame);
                } else {
                    strip.style.transform = "translateY(" + (-targetOffset) + "px)";
                    resolve();
                }
            }

            requestAnimationFrame(frame);
        });
    }

    async function spin() {
        if (spinning) return;
        spinning = true;
        spinBtn.disabled = true;
        spinBtn.classList.add("spinning");
        setControlsDisabled(true);
        resultsSection.style.display = "none";
        resultsContainer.innerHTML = "";

        const unplayedOnly = document.getElementById("unplayedToggle").checked;
        const excluded = Array.from(
            document.querySelectorAll(".category-pill:not(.active)")
        ).map(function (p) {
            return "&exclude_category=" + encodeURIComponent(p.dataset.category);
        }).join("");
        const url =
            SPIN_URL + "?count=" + REEL_COUNT + "&unplayed_only=" + unplayedOnly + excluded;

        let data;
        try {
            const resp = await fetch(url);
            data = await resp.json();
            if (!resp.ok) {
                alert(data.error || "Something went wrong");
                resetSpinState();
                return;
            }
        } catch (err) {
            alert("Network error — please try again");
            resetSpinState();
            return;
        }

        const results = data.games;

        // Rebuild reels with winning games injected
        const strips = reelsContainer.querySelectorAll(".reel-strip");
        const promises = [];

        for (let i = 0; i < strips.length; i++) {
            const strip = strips[i];
            strip.innerHTML = "";

            // Build a shuffled set of filler tiles
            const shuffled = shuffleArray(FILLER_POOL);

            // Place filler tiles, inject winner near the end
            const winnerIndex = TILES_IN_STRIP - 6;
            for (let t = 0; t < TILES_IN_STRIP; t++) {
                if (t === winnerIndex) {
                    strip.appendChild(createTile(results[i]));
                } else {
                    const filler = shuffled[t % shuffled.length];
                    strip.appendChild(createTile(filler));
                }
            }

            // Read actual tile height from rendered DOM (responsive sizes vary)
            const firstTile = strip.querySelector(".reel-tile");
            const tileHeight = firstTile ? firstTile.offsetHeight : 270;

            // Calculate target offset so winner tile is centered in window
            const windowHeight = strip.parentElement.clientHeight;
            const targetOffset =
                winnerIndex * tileHeight -
                windowHeight / 2 +
                tileHeight / 2;

            const duration = BASE_DURATION + i * STAGGER_MS;
            promises.push(animateReel(strip, targetOffset, duration, tileHeight));
        }

        await Promise.all(promises);

        // Show results
        showResults(results);
        resetSpinState();
    }

    function resetSpinState() {
        spinning = false;
        spinBtn.disabled = false;
        spinBtn.classList.remove("spinning");
        setControlsDisabled(false);
    }

    function setControlsDisabled(disabled) {
        document.getElementById("unplayedToggle").disabled = disabled;
        document.querySelectorAll(".category-pill").forEach(function (pill) {
            pill.disabled = disabled;
        });
    }

    // --- Results ---

    function showResults(games) {
        resultsContainer.innerHTML = "";

        games.forEach(function (game, idx) {
            const card = document.createElement("div");
            card.className = "result-card";
            card.style.animationDelay = idx * 0.15 + "s";

            let html = "";
            const imgSrc = game.image_url || PLACEHOLDER_IMG;
            html += '<img src="' + escapeHtml(imgSrc) + '" alt="' + escapeHtml(game.title) + '" onerror="this.src=\'' + PLACEHOLDER_IMG + '\'">';
            html += '<div class="card-body">';
            html += '<div class="card-title">' + escapeHtml(game.title) + "</div>";
            html += '<div class="card-developer">by ' + escapeHtml(game.developer) + "</div>";
            if (game.description) {
                html += '<div class="card-description">' + escapeHtml(game.description) + "</div>";
            }
            html += '<div class="card-links">';
            html += '<a href="' + DETAIL_URL_BASE + game.id + '/">Review</a>';
            html += ' &middot; ';
            html += '<a href="' + escapeHtml(game.game_url) + '" target="_blank" rel="noopener">itch.io</a>';
            html += "</div>";
            html += "</div>";

            card.innerHTML = html;
            resultsContainer.appendChild(card);
        });

        resultsSection.style.display = "block";
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    // --- Event listeners ---

    // Spin button
    spinBtn.addEventListener("click", spin);

    // Category pills toggle exclusion
    document.querySelectorAll(".category-pill").forEach(function (pill) {
        pill.addEventListener("click", function () {
            if (this.disabled) return;
            this.classList.toggle("active");
        });
    });

    // Rebuild reels on resize so tile sizing stays in sync with CSS breakpoints
    let resizeTimer;
    window.addEventListener("resize", function () {
        if (spinning) return;
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(buildReels, 200);
    });

    // Init
    buildReels();
})();
