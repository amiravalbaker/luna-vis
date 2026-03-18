console.log("visibility.js loaded");

/* -------------------------
   FORMATTERS
-------------------------- */

function formatTimeOnly(isoString, timeZone = "Europe/London") {
    if (!isoString) return "N/A";

    const date = new Date(isoString);

    return date.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone,
    });
}

function formatMoonAge(hours) {
    if (hours == null) return "N/A";

    if (hours < 24) {
        const wholeHours = Math.floor(hours);
        const minutes = Math.round((hours - wholeHours) * 60);
        return `${wholeHours} h ${minutes} m`;
    }

    return `${(hours / 24).toFixed(1)} days`;
}




/* -------------------------
   HERO
-------------------------- */

/*function updateVisibilityMoonImage(data) {
    const img = document.getElementById("visibility-moon-image");
    if (!img) return;

    img.src = getMoonImageForAgeHours(data.moon_age_hours);
    img.alt = "Moon visibility";
}*/

async function fetchVisibilityAnchorData() {
    const location = getSelectedLocationOrShowMessage("visibility-status");
    if (!location) return null;

    const currentDate = document.getElementById("date").value;
    const tz = location.tz || "UTC";
    const elevation_m = document.getElementById("elevation_m").value || location.elevation_m || 0;

    const params = new URLSearchParams({
        lat: location.lat,
        lon: location.lon,
        elevation_m,
        date: currentDate,
        tz,
    });

    return await apiGet(`/api/v1/visibility/?${params.toString()}`);
}

async function goToPreviousNewMoon() {
    const status = document.getElementById("visibility-status");

    try {
        const data = await fetchVisibilityAnchorData();
        if (!data || !data.previous_new_moon_date) return;

        setSelectedDateAndAnchor(data.previous_new_moon_date);
    } catch (error) {
        if (status) status.textContent = `Error: ${error.message}`;
    }
}

async function goToNextNewMoon() {
    const status = document.getElementById("visibility-status");

    try {
        const data = await fetchVisibilityAnchorData();
        if (!data || !data.next_new_moon_date) return;

        setSelectedDateAndAnchor(data.next_new_moon_date);
    } catch (error) {
        if (status) status.textContent = `Error: ${error.message}`;
    }
}


function ensureDateInputIsDateOnly() {
    const dateInput = document.getElementById("date");
    if (!dateInput || !dateInput.value) return;

    dateInput.value = String(dateInput.value).split("T")[0];
}


function renderVisibilityDateSummary(newMoonDate) {
    const el = document.getElementById("selected-date-summary");
    if (!el) return;

    el.innerHTML = `<strong>New Moon:</strong> ${newMoonDate ? formatDateLong(newMoonDate) : "N/A"}`;
}


function renderVisibilityHeroSummary(data, windowData) {
    const el = document.getElementById("visibility-phase-summary");
    if (!el) return;

    el.innerHTML = `
        <div class="phase-name">New Moon Visibility</div>
        <div class="phase-illumination">
            New Moon: ${windowData?.new_moon_date ? formatDateLong(windowData.new_moon_date) : "N/A"}
        </div>
        <div class="phase-illumination">
            Optimistic: ${windowData?.optimistic_date ? formatDateLong(windowData.optimistic_date) : "N/A"}
        </div>
        <div class="phase-illumination">
            Conservative: ${windowData?.conservative_date ? formatDateLong(windowData.conservative_date) : "N/A"}
        </div>
    `;
}

/* -------------------------
   SUMMARY CARDS
-------------------------- */

function renderVisibilitySummaryCards(data, windowData) {
    const container = document.getElementById("visibility-summary-cards");
    const tz = document.getElementById("tz")?.value || "UTC";

    container.innerHTML = `
        <div class="data-item data-item-centered">
            <div class="data-label">New Moon</div>
            <div class="data-value">${windowData?.new_moon_date ? formatDateLong(windowData.new_moon_date) : "N/A"}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">Optimistic Visibility</div>
            <div class="data-value">${windowData?.optimistic_date ? formatDateLong(windowData.optimistic_date) : "N/A"}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">Conservative Visibility</div>
            <div class="data-value">${windowData?.conservative_date ? formatDateLong(windowData.conservative_date) : "N/A"}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">Sunset</div>
            <div class="data-value">${formatTimeOnly(data.sunset_utc, tz)}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">Moonset</div>
            <div class="data-value">${formatTimeOnly(data.moonset_utc, tz)}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">Moon Age</div>
            <div class="data-value">${formatMoonAge(data.moon_age_hours)}</div>
        </div>
    `;
}


function renderVisibilityDateSummary(newMoonDate) {
    const el = document.getElementById("selected-date-summary");
    if (!el) return;

    el.innerHTML = `<strong>New Moon:</strong> ${newMoonDate ? formatDateLong(newMoonDate) : "N/A"}`;
}

/* -------------------------
   SELECTED DATE DETAIL
-------------------------- */

function renderVisibilityResults(data) {
    const container = document.getElementById("visibility-results");

    if (!data.within_visibility_window) {
        container.innerHTML = `
            <div class="data-item">
                <div class="data-label">Date</div>
                <div class="data-value">${formatDateLong(data.date_local)}</div>
            </div>
            <div class="data-item">
                <div class="data-label">Status</div>
                <div class="data-value">Outside visibility window</div>
            </div>
        `;
        return;
    }

    const criteriaHtml = (data.criteria || []).map(c => `
        <div class="data-item">
            <div class="data-label">${c.name}</div>
            <div class="data-value">${c.verdict}</div>
            <div class="data-label">Band: ${c.band ?? "N/A"}</div>
            <div class="data-label">Score: ${c.score == null ? "N/A" : c.score.toFixed(2)}</div>
            <div class="data-label">${c.reason}</div>
        </div>
    `).join("");

    container.innerHTML = criteriaHtml;
}

/* -------------------------
   5-DAY WINDOW
-------------------------- */

function renderWindowSummary(data) {
    const summaryContainer = document.getElementById("window-summary");

    summaryContainer.innerHTML = `
        <div class="data-item data-item-centered">
            <div class="data-label">Input Date</div>
            <div class="data-value">${data.selected_date ? formatDateLong(data.selected_date) : "N/A"}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">New Moon</div>
            <div class="data-value">${data.new_moon_date ? formatDateLong(data.new_moon_date) : "N/A"}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">Optimistic</div>
            <div class="data-value">${data.optimistic_date ? formatDateLong(data.optimistic_date) : "N/A"}</div>
        </div>

        <div class="data-item data-item-centered">
            <div class="data-label">Majority</div>
            <div class="data-value">${data.majority_date ? formatDateLong(data.majority_date) : "N/A"}</div>
        </div>

         <div class="data-item data-item-centered">
            <div class="data-label">Conservative</div>
            <div class="data-value">${data.conservative_date ? formatDateLong(data.conservative_date) : "N/A"}</div>
        </div>
    `;
}


function renderWindowTable(data) {
    const resultsContainer = document.getElementById("window-results");

    const rows = (data.results || []).map(n => `
        <tr>
            <td>${formatDateLong(n.date_local)}</td>
            <td>${formatMoonAge(n.age_hours)}</td>
            <td>${n.visible_count}</td>
            <td>${n.maybe_count}</td>
            <td>${n.not_visible_count}</td>
            <td>${(n.consensus_fraction * 100).toFixed(0)}%</td>
        </tr>
    `).join("");

    resultsContainer.innerHTML = `
        <table class="results-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Moon Age</th>
                    <th>Visible</th>
                    <th>Maybe</th>
                    <th>Not Visible</th>
                    <th>Consensus</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `;
}

/* -------------------------
   LOAD DATA
-------------------------- */

async function loadVisibilityForCurrentState() {
    const visibilityStatus = document.getElementById("visibility-status");
    const windowStatus = document.getElementById("window-status");

    const location = getSelectedLocationOrShowMessage("visibility-status");
    if (!location) {
        windowStatus.textContent = "";
        return;
    }

    const elevation_m = document.getElementById("elevation_m").value || location.elevation_m || 0;
    const date = document.getElementById("date").value;
    const tz = location.tz || "UTC";

    visibilityStatus.textContent = "Loading visibility...";
    windowStatus.textContent = "Loading window...";

    const visibilityParams = new URLSearchParams({
        lat: location.lat,
        lon: location.lon,
        elevation_m,
        date,
        tz,
    });

    const windowParams = new URLSearchParams({
        lat: location.lat,
        lon: location.lon,
        elevation_m,
        start_date: date,
        tz,
        nights: 5,
    });

    try {
        const [visibilityData, windowData] = await Promise.all([
            apiGet(`/api/v1/visibility/?${visibilityParams.toString()}`),
            apiGet(`/api/v1/visibility-window/?${windowParams.toString()}`),
        ]);

        renderVisibilityHeroSummary(visibilityData, windowData);
        renderVisibilityDateSummary(windowData.new_moon_date);
        renderVisibilitySummaryCards(visibilityData, windowData);
        renderVisibilityResults(visibilityData);
        renderWindowSummary(windowData);
        renderWindowTable(windowData);

        renderSelectedLocationSummary();

        visibilityStatus.textContent = "";
        windowStatus.textContent = "";
    } catch (error) {
        visibilityStatus.textContent = `Error: ${error.message}`;
        windowStatus.textContent = `Error: ${error.message}`;
    }
}

/* -------------------------
   FORM
-------------------------- */

async function handleVisibilityFormSubmit(event) {
    event.preventDefault();
    await loadVisibilityForCurrentState();
}

/* -------------------------
   INIT
-------------------------- */

document.addEventListener("DOMContentLoaded", async () => {
    applyStoredDateToPageFields();
    applyStoredLocationToPageFields();
    ensureDateInputIsDateOnly();

    renderSelectedLocationSummary();

    document.getElementById("visibility-form")
        ?.addEventListener("submit", handleVisibilityFormSubmit);

    document.getElementById("prev-date-btn")
        ?.addEventListener("click", goToPreviousNewMoon);

    document.getElementById("next-date-btn")
        ?.addEventListener("click", goToNextNewMoon);

    document.getElementById("date")
        ?.addEventListener("change", (event) => {
            const value = String(event.target.value || "").split("T")[0];
            if (value) {
                setSelectedDateAndAnchor(value);
            }
         });

    window.addEventListener("lunavis:location-changed", async () => {
        applyStoredLocationToPageFields();
        renderSelectedLocationSummary();
        ensureDateInputIsDateOnly();

        await loadVisibilityForCurrentState();
    });

    window.addEventListener("lunavis:date-changed", async () => {
        applyStoredDateToPageFields();
        ensureDateInputIsDateOnly();

        await loadVisibilityForCurrentState();
    });

    if (loadSelectedLocation()) {
        await loadVisibilityForCurrentState();
    }
});