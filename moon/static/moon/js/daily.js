console.log("daily.js loaded");

/* -------------------------
   FORMATTERS
-------------------------- */

function formatTimeOnly(isoString, timeZone = "Europe/London") {
    if (!isoString) return "N/A";

    const safeTimeZone = isValidIanaTimeZone(timeZone) ? timeZone : "UTC";

    const date = new Date(isoString);

    return date.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: safeTimeZone,
    });
}

function isValidIanaTimeZone(value) {
    if (!value) return false;
    try {
        Intl.DateTimeFormat("en-GB", { timeZone: value }).format(new Date());
        return true;
    } catch {
        return false;
    }
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

function formatTownCountry(location) {
    if (!location?.display_name) return "N/A";

    const parts = location.display_name
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean);

    if (parts.length === 0) return "N/A";
    if (parts.length === 1) return parts[0];

    const country = parts[parts.length - 1];
    const noisePattern = /\d|street|st\.?|road|rd\.?|avenue|ave\.?|jalan|lot|block|building|floor|postcode|postal|district|county|province|state|region|municipality/i;
    const locality = parts.find((part) => !noisePattern.test(part)) || parts[0];

    return `${locality}, ${country}`;
}

/* -------------------------
   RENDER RESULTS
-------------------------- */

function renderResults(data) {
    const results = document.getElementById("results");
    const tz = isValidIanaTimeZone(data?.tz) ? data.tz : "UTC";
    const location = loadSelectedLocation();
    const selectedDate = data?.date_local || loadSelectedDate();

    results.innerHTML = `
        <div class="row g-3">
            <div class="col-12 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/location.svg" alt="Location" class="data-icon-img">
                    <div class="data-label">Location</div>
                    <div class="data-value">${formatTownCountry(location)}</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/timezone.svg" alt="Timezone" class="data-icon-img">
                    <div class="data-label">Timezone</div>
                    <div class="data-value">${location?.tz_label || location?.tz || tz}</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/elevation.svg" alt="Elevation" class="data-icon-img">
                    <div class="data-label">Elevation</div>
                    <div class="data-value">${location?.elevation_m ?? 0} m</div>
                </div>
            </div>

            <div class="col-12 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/calendar.svg" alt="Selected Date" class="data-icon-img">
                    <div class="data-label">Selected Date</div>
                    <div class="data-value">${selectedDate ? formatDateLong(selectedDate) : "N/A"}</div>
                </div>
            </div>
        </div>

        <div class="row g-3 mt-1">
            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/sunrise.png" alt="Sunrise" class="data-icon-img data-icon-img-sun-event">
                    <div class="data-label">Sunrise</div>
                    <div class="data-value">${formatTimeOnly(data.sunrise_utc, tz)}</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/sunset.png" alt="Sunset" class="data-icon-img data-icon-img-sun-event">
                    <div class="data-label">Sunset</div>
                    <div class="data-value">${formatTimeOnly(data.sunset_utc, tz)}</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moonrise.png" alt="Moonrise" class="data-icon-img">
                    <div class="data-label">Moonrise</div>
                    <div class="data-value">${formatTimeOnly(data.moonrise_utc, tz)}</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moonset.png" alt="Moonset" class="data-icon-img">
                    <div class="data-label">Moonset</div>
                    <div class="data-value">${formatTimeOnly(data.moonset_utc, tz)}</div>
                </div>
            </div>
        </div>

        <div class="row g-3 mt-1">
            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/sun.png" alt="Sun" class="data-icon-img">
                    <div class="data-label">Altitude</div>
                    <div class="data-value">${data.sun_alt_deg?.toFixed(2)}°</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/sun.png" alt="Sun" class="data-icon-img">
                    <div class="data-label">Azimuth</div>
                    <div class="data-value">${data.sun_az_deg?.toFixed(2)}°</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moon.png" alt="Moon" class="data-icon-img">
                    <div class="data-label">Altitude</div>
                    <div class="data-value">${data.moon_alt_deg?.toFixed(2)}°</div>
                </div>
            </div>

            <div class="col-6 col-lg-3">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moon.png" alt="Moon" class="data-icon-img">
                    <div class="data-label">Azimuth</div>
                    <div class="data-value">${data.moon_az_deg?.toFixed(2)}°</div>
                </div>
            </div>
        </div>

        <div class="row g-3 mt-1">
            <div class="col-6">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moon.png" alt="Moon" class="data-icon-img">
                    <div class="data-label">Moon Age</div>
                    <div class="data-value">${formatMoonAge(data.moon_age_hours)}</div>
                </div>
            </div>

            <div class="col-6">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moon.png" alt="Moon" class="data-icon-img">
                    <div class="data-label">Moon Distance</div>
                    <div class="data-value">${formatMillionMiles(data.moon_distance_km)}</div>
                </div>
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
    const tz = isValidIanaTimeZone(location?.tz) ? location.tz : "UTC";

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

    // Daily page should always start from today's date.
    setSelectedDateAndAnchor(getTodayDateString());

    applyStoredDateToPageFields();
    applyStoredLocationToPageFields();

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

        await loadDailyDataForCurrentState();

    });

    window.addEventListener("lunavis:date-changed", async () => {

        applyStoredDateToPageFields();

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
        return "/static/moon/img/moon-day-07.png";
    }

    const synodicDays = 29.53;
    const ageDays = ageHours / 24;
    let index = Math.round((ageDays / synodicDays) * 28) + 1;

    if (index < 1) index = 1;
    if (index > 29) index = 29;

    return `/static/moon/img/moon-day-${String(index).padStart(2, "0")}.png`;
}

function updateMoonPhaseImage(data) {
    const img = document.getElementById("moon-phase-image");
    if (!img) return;

    img.src = getMoonImageForAgeHours(data.moon_age_hours);
    img.alt = data.phase_name || "Moon phase";
}