console.log("visibility.js loaded");

/* -------------------------
   PAGE-LOCAL LUNATION STATE
-------------------------- */

let currentVisibilityAnchorDate = null;
let currentPreviousNewMoonDate = null;
let currentNextNewMoonDate = null;

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

    const sign = hours < 0 ? "-" : "";
    const absHours = Math.abs(hours);

    if (absHours < 24) {
        const wholeHours = Math.floor(absHours);
        const minutes = Math.round((absHours - wholeHours) * 60);
        return `${sign}${wholeHours} h ${minutes} m`;
    }

    return `${sign}${(absHours / 24).toFixed(1)} days`;
}

function safeFormatDateLong(dateString) {
    if (typeof formatDateLong === "function") {
        return formatDateLong(dateString);
    }

    if (!dateString) return "N/A";
    return String(dateString);
}

function ensureDateInputIsDateOnly() {
    const dateInput = document.getElementById("date");
    if (!dateInput || !dateInput.value) return;

    dateInput.value = String(dateInput.value).split("T")[0];
}

/* -------------------------
   HERO
-------------------------- */

function renderVisibilityDateSummary(newMoonDate) {
    const el = document.getElementById("selected-date-summary");
    if (!el) return;

    el.innerHTML = `<strong>Date:</strong> ${newMoonDate ? safeFormatDateLong(newMoonDate) : "N/A"}`;
}

function getFirstConsensusDate(windowData) {
    if (!windowData) return null;
    return windowData.first_100_consensus_date || windowData.conservative_date || null;
}

function getFirstConsensusMoonAge(windowData) {
    const firstConsensusDate = getFirstConsensusDate(windowData);
    if (!firstConsensusDate || !Array.isArray(windowData?.results)) return null;

    const consensusNight = windowData.results.find(
        (night) => night?.date_local === firstConsensusDate
    );

    return consensusNight?.age_hours ?? null;
}

function getFirstConsensusNight(windowData) {
    const firstConsensusDate = getFirstConsensusDate(windowData);
    if (!firstConsensusDate || !Array.isArray(windowData?.results)) return null;

    return windowData.results.find(
        (night) => night?.date_local === firstConsensusDate
    ) || null;
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

    const locality =
        parts.find((part) => !noisePattern.test(part)) ||
        parts[0];

    return `${locality}, ${country}`;
}

function normalizeUtcOffsetLabel(offsetLabel) {
    if (!offsetLabel) return "UTC+0";

    const normalized = String(offsetLabel).replace("GMT", "UTC");
    const match = normalized.match(/^UTC([+-])(\d{1,2})(?::?(\d{2}))?$/i);
    if (!match) return normalized;

    const sign = match[1];
    const hours = String(parseInt(match[2], 10));
    const minutes = match[3] || "00";

    if (minutes === "00") {
        return `UTC${sign}${hours}`;
    }

    return `UTC${sign}${hours}:${minutes}`;
}

function getUtcOffsetLabelForTimezone(tzName) {
    if (!isValidIanaTimeZone(tzName)) return "UTC+0";

    try {
        const parts = new Intl.DateTimeFormat("en-GB", {
            timeZone: tzName,
            timeZoneName: "shortOffset",
        }).formatToParts(new Date());

        const rawOffset = parts.find((p) => p.type === "timeZoneName")?.value;
        return normalizeUtcOffsetLabel(rawOffset || "UTC+0");
    } catch {
        return "UTC+0";
    }
}

function formatTimezoneShort(location, fallbackTz = "UTC") {
    const tzName = location?.tz || fallbackTz || "UTC";
    const label = location?.tz_label;

    if (label) {
        const seasonalMatch = String(label).match(/^(.+?)\s+\((?:winter|spring|summer|autumn)\)\s+\((UTC[+-]\d+(?::\d{2})?)\)$/i);
        if (seasonalMatch) {
            return `${seasonalMatch[1]} (${normalizeUtcOffsetLabel(seasonalMatch[2])})`;
        }

        const shortMatch = String(label).match(/^(.+?)\s+\((UTC[+-]\d+(?::\d{2})?)\)$/i);
        if (shortMatch) {
            return `${shortMatch[1]} (${normalizeUtcOffsetLabel(shortMatch[2])})`;
        }
    }

    const city = tzName.includes("/") ? tzName.split("/").pop().replaceAll("_", " ") : tzName;
    const offset = getUtcOffsetLabelForTimezone(tzName);
    return `${city} (${offset})`;
}

function renderVisibilityHeroSummary(visibilityData, windowData) {
    const el = document.getElementById("visibility-phase-summary");
    if (!el) return;

    // Keep hero area focused on moon image; summary lines render in the card below.
    el.innerHTML = "";
}

/* -------------------------
   SUMMARY CARDS
-------------------------- */

function renderVisibilitySummaryCards(data, windowData) {
    const container = document.getElementById("visibility-summary-cards");
    if (!container) return;

    const rawTz = document.getElementById("tz")?.value;
    const tz = isValidIanaTimeZone(rawTz) ? rawTz : "UTC";
    const location = loadSelectedLocation();
    const firstConsensusDate = getFirstConsensusDate(windowData);
    const firstConsensusNight = getFirstConsensusNight(windowData);
    const consensusMoonAgeHours = getFirstConsensusMoonAge(windowData);
    const consensusSunsetUtc = firstConsensusNight?.sunset_utc || data?.sunset_utc;
    const consensusMoonsetUtc = firstConsensusNight?.moonset_utc || data?.moonset_utc;
    const consensusText = firstConsensusDate ? safeFormatDateLong(firstConsensusDate) : "Not reached in current window";
    const conjunctionUtc = windowData?.new_moon_conjunction_utc || data?.new_moon_conjunction_utc;
    const conjunctionText = `${windowData?.new_moon_date ? safeFormatDateLong(windowData.new_moon_date) : "N/A"} @${conjunctionUtc ? formatTimeOnly(conjunctionUtc, tz) : "N/A"}`;

    container.innerHTML = `
        <div class="row g-3">
            <div class="col-12">
                <div class="data-item data-item-centered visibility-new-moon-line">
                    <span class="visibility-consensus-title">New Moon Conjunction:</span>
                    <span class="visibility-consensus-value">${conjunctionText}</span>
                </div>
            </div>

            <div class="col-12 col-md-4">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/location.svg" alt="Location" class="data-icon-img">
                    <div class="data-label">Location</div>
                    <div class="data-value">${formatTownCountry(location)}</div>
                </div>
            </div>

            <div class="col-6 col-md-4">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/timezone.svg" alt="Timezone" class="data-icon-img">
                    <div class="data-label">Timezone</div>
                    <div class="data-value">${formatTimezoneShort(location, tz)}</div>
                </div>
            </div>

            <div class="col-6 col-md-4">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/elevation.svg" alt="Elevation" class="data-icon-img">
                    <div class="data-label">Elevation</div>
                    <div class="data-value">${location?.elevation_m ?? 0} m</div>
                </div>
            </div>

            <div class="col-12">
                <div class="visibility-consensus-line">
                    <span class="visibility-consensus-title">New Crescent Moon Visibility:</span>
                    <span class="visibility-consensus-value">${consensusText}.</span>
                </div>
            </div>

            <div class="col-6 col-md-4">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/sunset.png" alt="Sunset" class="data-icon-img data-icon-img-sun-event">
                    <div class="data-label">Sunset</div>
                    <div class="data-value">${formatTimeOnly(consensusSunsetUtc, tz)}</div>
                </div>
            </div>

            <div class="col-6 col-md-4">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moonset.png" alt="Moonset" class="data-icon-img">
                    <div class="data-label">Moonset</div>
                    <div class="data-value">${formatTimeOnly(consensusMoonsetUtc, tz)}</div>
                </div>
            </div>

            <div class="col-12 col-md-4">
                <div class="data-item data-item-centered h-100">
                    <img src="/static/moon/img/icons/moon.png" alt="Moon" class="data-icon-img">
                    <div class="data-label">Moon Age</div>
                    <div class="data-value">${formatMoonAge(consensusMoonAgeHours ?? data?.moon_age_hours)}</div>
                </div>
            </div>
        </div>
    `;
}

/* -------------------------
   SELECTED DATE DETAIL
-------------------------- */

function renderVisibilityResults(data) {
    const container = document.getElementById("visibility-results");
    if (!container) return;

    if (!data.within_visibility_window) {
        container.innerHTML = `
            <div class="row g-3">
                <div class="col-12 col-md-6">
                    <div class="data-item h-100">
                        <div class="data-label">Date</div>
                        <div class="data-value">${formatDateLong(data.date_local)}</div>
                    </div>
                </div>
                <div class="col-12 col-md-6">
                    <div class="data-item h-100">
                        <div class="data-label">Status</div>
                        <div class="data-value">Outside visibility window</div>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    const criteriaHtml = (data.criteria || []).map(c => `
        <div class="col-12 col-md-6 col-xl-4">
            <div class="data-item h-100">
                <div class="data-label">${c.name}</div>
                <div class="data-value">${c.verdict}</div>
                <div class="data-label">Band: ${c.band ?? "N/A"}</div>
                <div class="data-label">Score: ${c.score == null ? "N/A" : c.score.toFixed(2)}</div>
                <div class="data-label">${c.reason}</div>
            </div>
        </div>
    `).join("");

    container.innerHTML = `<div class="row g-3">${criteriaHtml}</div>`;
}

/* -------------------------
   5-DAY WINDOW
-------------------------- */

function renderWindowSummary(data) {
    const summaryContainer = document.getElementById("window-summary");
    if (!summaryContainer) return;

    const nights = Array.isArray(data?.results) ? data.results.slice(0, 5) : [];
    while (nights.length < 5) {
        nights.push(null);
    }

    function getCriterion(night, criterionKey) {
        if (!night || !Array.isArray(night.criteria)) return null;
        return night.criteria.find((c) => (c?.criterion_id || "").toLowerCase().includes(criterionKey));
    }

    function getCriterionOrOutsideWindow(night, criterionKey) {
        const criterion = getCriterion(night, criterionKey);
        if (criterion) return criterion;

        // For valid nights where criteria are omitted (outside 0-120h window),
        // show explicit non-visibility values instead of N/A.
        if (night) {
            return {
                verdict: "NOT_VISIBLE",
                reason: "Outside visibility window",
                band: "N/A",
                score: null,
            };
        }

        return null;
    }

    function cellValue(renderer) {
        return nights
            .map((night) => `<td>${renderer(night)}</td>`)
            .join("");
    }

    function formatVerdict(verdict) {
        if (!verdict) return "N/A";

        const text = String(verdict).toLowerCase().replaceAll("_", " ");
        return text.charAt(0).toUpperCase() + text.slice(1);
    }

    summaryContainer.innerHTML = `
        <div class="table-responsive">
            <table class="results-table">
                <tbody>
                    <tr>
                        <th>Date</th>
                        ${cellValue((night) => night?.date_local ? safeFormatDateLong(night.date_local) : "N/A")}
                    </tr>
                    <tr>
                        <th>Yallop</th>
                        ${cellValue((night) => {
                            const c = getCriterionOrOutsideWindow(night, "yallop");
                            return formatVerdict(c?.verdict);
                        })}
                    </tr>
                    <tr>
                        <th>Reasons</th>
                        ${cellValue((night) => {
                            const c = getCriterionOrOutsideWindow(night, "yallop");
                            return c?.reason || "N/A";
                        })}
                    </tr>
                    <tr>
                        <th>Band</th>
                        ${cellValue((night) => {
                            const c = getCriterionOrOutsideWindow(night, "yallop");
                            return c?.band || "N/A";
                        })}
                    </tr>
                    <tr>
                        <th>Score</th>
                        ${cellValue((night) => {
                            const c = getCriterionOrOutsideWindow(night, "yallop");
                            return c?.score == null ? "N/A" : Number(c.score).toFixed(2);
                        })}
                    </tr>
                    <tr>
                        <th>Odeh</th>
                        ${cellValue((night) => {
                            const c = getCriterionOrOutsideWindow(night, "odeh");
                            return formatVerdict(c?.verdict);
                        })}
                    </tr>
                    <tr>
                        <th>Reasons</th>
                        ${cellValue((night) => {
                            const c = getCriterionOrOutsideWindow(night, "odeh");
                            return c?.reason || "N/A";
                        })}
                    </tr>
                    <tr>
                        <th>Band</th>
                        ${cellValue((night) => {
                            const c = getCriterionOrOutsideWindow(night, "odeh");
                            return c?.band || "N/A";
                        })}
                    </tr>
                    <tr>
                        <th>Visibility Consensus</th>
                        ${cellValue((night) => night ? `${(Number(night.consensus_fraction || 0) * 100).toFixed(0)}%` : "N/A")}
                    </tr>
                </tbody>
            </table>
        </div>
    `;
}

function renderWindowTable(data) {
    const resultsContainer = document.getElementById("window-results");
    if (!resultsContainer) return;

    const rows = (data.results || []).map(n => `
        <tr>
            <td>${safeFormatDateLong(n.date_local)}</td>
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
   NEW MOON NAVIGATION
-------------------------- */

async function goToPreviousNewMoon() {
    const status = document.getElementById("visibility-status");

    if (!currentPreviousNewMoonDate) {
        if (status) status.textContent = "No earlier new moon available in the current range.";
        return;
    }

    const dateInput = document.getElementById("date");
    if (dateInput) {
        dateInput.value = currentPreviousNewMoonDate;
    }

    await loadVisibilityForCurrentState();
}

async function goToNextNewMoon() {
    const status = document.getElementById("visibility-status");

    if (!currentNextNewMoonDate) {
        if (status) status.textContent = "No later new moon available in the current range.";
        return;
    }

    const dateInput = document.getElementById("date");
    if (dateInput) {
        dateInput.value = currentNextNewMoonDate;
    }

    await loadVisibilityForCurrentState();
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
    const date = String(document.getElementById("date").value || "").split("T")[0];
    const tz = isValidIanaTimeZone(location?.tz) ? location.tz : "UTC";

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

        // Store page-local lunation navigation state
        currentVisibilityAnchorDate = windowData.new_moon_date || null;
        currentPreviousNewMoonDate = visibilityData.previous_new_moon_date || null;
        currentNextNewMoonDate = visibilityData.next_new_moon_date || null;

        const dateInput = document.getElementById("date");
        if (dateInput && windowData.new_moon_date) {
            dateInput.value = windowData.new_moon_date;
        }

        const runRender = (fn, label) => {
            try {
                fn();
            } catch (error) {
                console.error(`Visibility render failed (${label}):`, error);
            }
        };

        runRender(() => renderVisibilityHeroSummary(visibilityData, windowData), "hero");
        runRender(() => renderVisibilityDateSummary(windowData.new_moon_date), "date-summary");
        runRender(() => renderVisibilitySummaryCards(visibilityData, windowData), "summary-cards");
        runRender(() => renderVisibilityResults(visibilityData), "criteria");
        runRender(() => renderWindowSummary(windowData), "window-summary");
        runRender(() => renderWindowTable(windowData), "window-table");

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
        ?.addEventListener("change", async (event) => {
            const value = String(event.target.value || "").split("T")[0];
            if (value) {
                event.target.value = value;
                await loadVisibilityForCurrentState();
            }
        });

    window.addEventListener("lunavis:location-changed", async () => {
        applyStoredLocationToPageFields();
        renderSelectedLocationSummary();
        ensureDateInputIsDateOnly();
        await loadVisibilityForCurrentState();
    });

    // When global date changes from nav/calendar, load visibility from that selected date
    window.addEventListener("lunavis:date-changed", async () => {
        applyStoredDateToPageFields();
        ensureDateInputIsDateOnly();
        await loadVisibilityForCurrentState();
    });

    if (loadSelectedLocation()) {
        await loadVisibilityForCurrentState();
    }
});