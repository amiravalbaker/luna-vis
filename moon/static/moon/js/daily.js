console.log("daily.js loaded");

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
        const whole = Math.floor(hours);
        const minutes = Math.round((hours - whole) * 60);
        return `${whole} h ${minutes} m`;
    }

    return `${(hours / 24).toFixed(1)} days`;
}

function formatMillionMiles(km) {
    if (km == null) return "N/A";

    const millionMiles = (km * 0.621371) / 1000000;
    return `${millionMiles.toFixed(3)} million miles`;
}

function formatIllumination(fraction) {
    if (fraction == null) return "N/A";
    return `${Math.max(0, Math.min(100, fraction * 100)).toFixed(1)}%`;
}

/* -------------------------
   RENDER RESULTS
-------------------------- */

function renderResults(data) {
    const results = document.getElementById("results");
    const tz = data.tz || "UTC";

    results.innerHTML = `
        <div class="daily-row daily-row-times">
            <div class="data-item data-item-centered">
                <div class="data-icon">🌅</div>
                <div class="data-label">Sunrise</div>
                <div class="data-value">${formatTimeOnly(data.sunrise_utc, tz)}</div>
            </div>

            <div class="data-item data-item-centered">
                <div class="data-icon">🌇</div>
                <div class="data-label">Sunset</div>
                <div class="data-value">${formatTimeOnly(data.sunset_utc, tz)}</div>
            </div>

            <div class="data-item data-item-centered">
                <div class="data-icon">🌙</div>
                <div class="data-label">Moonrise</div>
                <div class="data-value">${formatTimeOnly(data.moonrise_utc, tz)}</div>
            </div>

            <div class="data-item data-item-centered">
                <div class="data-icon">🌘</div>
                <div class="data-label">Moonset</div>
                <div class="data-value">${formatTimeOnly(data.moonset_utc, tz)}</div>
            </div>
        </div>

        <div class="daily-row daily-row-angles">
            <div class="data-item">
                <div class="data-label">Sun Altitude</div>
                <div class="data-value">${data.sun_alt_deg?.toFixed(2)}°</div>
            </div>

            <div class="data-item">
                <div class="data-label">Sun Azimuth</div>
                <div class="data-value">${data.sun_az_deg?.toFixed(2)}°</div>
            </div>

            <div class="data-item">
                <div class="data-label">Moon Altitude</div>
                <div class="data-value">${data.moon_alt_deg?.toFixed(2)}°</div>
            </div>

            <div class="data-item">
                <div class="data-label">Moon Azimuth</div>
                <div class="data-value">${data.moon_az_deg?.toFixed(2)}°</div>
            </div>
        </div>

        <div class="daily-row daily-row-final">
            <div class="data-item">
                <div class="data-label">Moon Age</div>
                <div class="data-value">${formatMoonAge(data.moon_age_hours)}</div>
            </div>

            <div class="data-item">
                <div class="data-label">Moon Distance</div>
                <div class="data-value">${formatMillionMiles(data.moon_distance_km)}</div>
            </div>
        </div>
    `;

    renderMoonPhaseSummary(data);
    updateMoonPhaseImage(data);
}


function renderMoonPhaseSummary(data) {
    const el = document.getElementById("moon-phase-summary");
    if (!el) return;

    el.innerHTML = `
        <div class="phase-name">${data.phase_name || "Moon Phase"}</div>
        <div class="phase-illumination">Illumination: ${formatIllumination(data.illumination_fraction)}</div>
    `;
}

/* -------------------------
   LOAD DATA
-------------------------- */

async function loadDailyDataForCurrentState() {

    const status = document.getElementById("status");

    const location = getSelectedLocationOrShowMessage("status");
    if (!location) return;

    const date = document.getElementById("date").value;
    const tz = location.tz || "UTC";

    status.textContent = "Loading...";

    const params = new URLSearchParams({
        lat: location.lat,
        lon: location.lon,
        elevation_m: location.elevation_m || 0,
        date,
        tz
    });

    try {

        const data = await apiGet(`/api/v1/daily/?${params.toString()}`);

        renderResults(data);
        updateMoonPhaseImage(data);
        renderSelectedLocationSummary();
        renderSelectedDateSummary();

        status.textContent = "";

    } catch (error) {

        status.textContent = `Error: ${error.message}`;

    }
}

/* -------------------------
   FORM
-------------------------- */

async function handleDailyFormSubmit(event) {
    event.preventDefault();
    await loadDailyDataForCurrentState();
}

/* -------------------------
   INIT
-------------------------- */

document.addEventListener("DOMContentLoaded", async () => {

    applyStoredDateToPageFields();
    applyStoredLocationToPageFields();

    renderSelectedLocationSummary();
    renderSelectedDateSummary();

    document
        .getElementById("daily-form")
        ?.addEventListener("submit", handleDailyFormSubmit);

    document
        .getElementById("prev-date-btn")
        ?.addEventListener("click", () => changeDateByDays(-1));

    document
        .getElementById("next-date-btn")
        ?.addEventListener("click", () => changeDateByDays(1));

    document
        .getElementById("date")?.
        addEventListener("change", (event) => {const value = event.target.value;
            if (value) {
                setSelectedDateAndAnchor(value);
                }
        });

    window.addEventListener("lunavis:location-changed", async () => {

        applyStoredLocationToPageFields();
        renderSelectedLocationSummary();

        await loadDailyDataForCurrentState();

    });

    window.addEventListener("lunavis:date-changed", async () => {

        applyStoredDateToPageFields();
        renderSelectedDateSummary();

        await loadDailyDataForCurrentState();

    });

    if (loadSelectedLocation()) {
        await loadDailyDataForCurrentState();
    }

});

/* -------------------------
IMAGES
-------------------------- */

function getMoonImageForAgeHours(ageHours) {
    if (ageHours == null) {
        return "/static/moon/img/moon-placeholder.jpg";
    }

    const synodicDays = 29.53;
    const ageDays = ageHours / 24;
    let index = Math.round((ageDays / synodicDays) * 28) + 1;

    if (index < 1) index = 1;
    if (index > 29) index = 29;

    return `/static/moon/img/moon-day-${String(index).padStart(2, "0")}.jpg`;
}

function updateMoonPhaseImage(data) {
    const img = document.getElementById("moon-phase-image");
    if (!img) return;

    img.src = getMoonImageForAgeHours(data.moon_age_hours);
    img.alt = data.phase_name || "Moon phase";
}