(function () {
    "use strict";

    var table = document.getElementById("gameListTable");
    var headers = table.querySelectorAll("th.sortable");
    var tbody = table.querySelector("tbody");
    var allRows = Array.from(tbody.querySelectorAll("tr"));

    var searchInput = document.getElementById("searchInput");
    var bundleFilter = document.getElementById("bundleFilter");
    var categoryFilter = document.getElementById("categoryFilter");
    var ratingFilter = document.getElementById("ratingFilter");
    var platformFilter = document.getElementById("platformFilter");
    var clearBtn = document.getElementById("clearFilters");
    var visibleCount = document.getElementById("visibleCount");
    var emptyState = document.getElementById("emptyState");

    // --- Filtering ---

    function applyFilters() {
        var query = searchInput.value.trim().toLowerCase();
        var bundleId = bundleFilter.value;
        var category = categoryFilter.value;
        var rating = ratingFilter.value;
        var platform = platformFilter.value;

        var visible = 0;
        allRows.forEach(function (row) {
            var title = row.dataset.title || "";
            var developer = row.dataset.developer || "";
            var bundles = (row.dataset.bundles || "").split(",");
            var rowCategory = row.dataset.category || "";
            var platforms = (row.dataset.platforms || "").split(",");
            var rowRating = row.dataset.rating || "0";

            var matchesQuery =
                !query || title.indexOf(query) !== -1 || developer.indexOf(query) !== -1;
            var matchesBundle = !bundleId || bundles.indexOf(bundleId) !== -1;
            var matchesCategory = !category || rowCategory === category;
            var matchesRating = rating === "" || rowRating === rating;
            var matchesPlatform = !platform || platforms.indexOf(platform) !== -1;

            var show = matchesQuery && matchesBundle && matchesCategory && matchesRating && matchesPlatform;
            row.style.display = show ? "" : "none";
            if (show) visible++;
        });

        visibleCount.textContent = visible;
        emptyState.style.display = visible === 0 ? "block" : "none";

        // Re-number visible rows
        var counter = 1;
        allRows.forEach(function (row) {
            if (row.style.display !== "none") {
                row.children[0].textContent = counter++;
            }
        });
    }

    searchInput.addEventListener("input", applyFilters);
    bundleFilter.addEventListener("change", applyFilters);
    categoryFilter.addEventListener("change", applyFilters);
    ratingFilter.addEventListener("change", applyFilters);
    platformFilter.addEventListener("change", applyFilters);

    clearBtn.addEventListener("click", function () {
        searchInput.value = "";
        bundleFilter.value = "";
        categoryFilter.value = "";
        ratingFilter.value = "";
        platformFilter.value = "";
        applyFilters();
    });

    // --- Sorting ---

    headers.forEach(function (th) {
        th.addEventListener("click", function () {
            var colIdx = parseInt(th.dataset.col);
            var sortType = th.dataset.sort;
            var ascending = !th.classList.contains("sorted-asc");

            headers.forEach(function (h) {
                h.classList.remove("sorted-asc", "sorted-desc");
            });
            th.classList.add(ascending ? "sorted-asc" : "sorted-desc");

            allRows.sort(function (a, b) {
                var cellA = a.children[colIdx];
                var cellB = b.children[colIdx];
                var valA, valB;

                if (sortType === "num") {
                    valA = parseInt(cellA.textContent.trim()) || 0;
                    valB = parseInt(cellB.textContent.trim()) || 0;
                    return ascending ? valA - valB : valB - valA;
                }

                if (sortType === "rating") {
                    valA = parseInt(a.dataset.rating);
                    valB = parseInt(b.dataset.rating);
                    return ascending ? valA - valB : valB - valA;
                }

                // alpha
                valA = cellA.textContent.trim().toLowerCase();
                valB = cellB.textContent.trim().toLowerCase();
                if (valA < valB) return ascending ? -1 : 1;
                if (valA > valB) return ascending ? 1 : -1;
                return 0;
            });

            // Re-attach in sorted order, then re-number visible rows
            allRows.forEach(function (row) {
                tbody.appendChild(row);
            });
            applyFilters();
        });
    });
})();
