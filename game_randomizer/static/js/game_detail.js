(function () {
    "use strict";

    let currentRating = INITIAL_RATING;
    const stars = document.querySelectorAll("#starRating .star");
    const ratingLabel = document.getElementById("ratingLabel");
    const notesField = document.getElementById("reviewNotes");
    const saveBtn = document.getElementById("saveReviewBtn");
    const saveStatus = document.getElementById("saveStatus");

    function updateStars(rating) {
        stars.forEach(function (star) {
            const val = parseInt(star.dataset.value);
            star.classList.toggle("active", rating !== null && val <= rating);
        });
        ratingLabel.textContent = rating ? rating + " / 3" : "Not rated";
    }

    // Initialize stars from existing review
    updateStars(currentRating);

    // Hover effect
    stars.forEach(function (star) {
        star.addEventListener("mouseenter", function () {
            const hoverVal = parseInt(this.dataset.value);
            stars.forEach(function (s) {
                s.classList.toggle("hovered", parseInt(s.dataset.value) <= hoverVal);
            });
        });

        star.addEventListener("mouseleave", function () {
            stars.forEach(function (s) {
                s.classList.remove("hovered");
            });
        });

        star.addEventListener("click", function () {
            const clickedVal = parseInt(this.dataset.value);
            // Clicking the active star again clears the rating
            if (currentRating === clickedVal) {
                currentRating = null;
            } else {
                currentRating = clickedVal;
            }
            updateStars(currentRating);
        });
    });

    // Save review
    saveBtn.addEventListener("click", async function () {
        saveBtn.disabled = true;

        const formData = new FormData();
        formData.append("rating", currentRating !== null ? currentRating : "");
        formData.append("notes", notesField.value);

        try {
            const resp = await fetch(SAVE_URL, {
                method: "POST",
                headers: { "X-CSRFToken": CSRF_TOKEN },
                body: formData,
            });
            const data = await resp.json();
            if (resp.ok) {
                showStatus("Saved!");
            } else {
                showStatus(data.error || "Error saving");
            }
        } catch (err) {
            showStatus("Network error");
        }

        saveBtn.disabled = false;
    });

    function showStatus(msg) {
        saveStatus.textContent = msg;
        saveStatus.classList.add("visible");
        setTimeout(function () {
            saveStatus.classList.remove("visible");
        }, 2000);
    }
})();
