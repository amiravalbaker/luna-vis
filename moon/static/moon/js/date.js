console.log("date.js loaded");

const DATE_STORAGE_KEY = "lunavis_selected_date";
const DATE_ANCHOR_KEY = "lunavis_anchor_date";
const DATE_WINDOW_DAYS = 16;

/* -------------------------
   HELPERS
-------------------------- */

function getTodayDateString() {
    return new Date().toISOString().split("T")[0];
}

function ordinal(n) {
    const s = ["th", "st", "nd", "rd"];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function formatDateLong(dateString) {
    if (!dateString) return "Not set";

    const [year, month, day] = dateString.split("-").map(Number);
    const date = new Date(Date.UTC(year, month - 1, day));

    const dayNum = ordinal(date.getUTCDate());
    const monthName = date.toLocaleString("en-GB", { month: "long", timeZone: "UTC" });
    const yearNum = date.getUTCFullYear();

    return `${dayNum} ${monthName} ${yearNum}`;
}


/* -------------------------
   STORAGE
-------------------------- */

function saveSelectedDate(dateString) {
    localStorage.setItem(DATE_STORAGE_KEY, dateString);
    updateCurrentDateLabel();
    updateDateArrowState();

    window.dispatchEvent(
        new CustomEvent("lunavis:date-changed", {
            detail: { date: dateString }
        })
    );
}

function loadSelectedDate() {
    return localStorage.getItem(DATE_STORAGE_KEY) || getTodayDateString();
}

function saveAnchorDate(dateString) {
    localStorage.setItem(DATE_ANCHOR_KEY, dateString);
}

function loadAnchorDate() {
    return localStorage.getItem(DATE_ANCHOR_KEY) || loadSelectedDate();
}

function setSelectedDateAndAnchor(dateString) {
    saveAnchorDate(dateString);
    saveSelectedDate(dateString);
}

function clearSelectedDate() {
    localStorage.removeItem(DATE_STORAGE_KEY);
    localStorage.removeItem(DATE_ANCHOR_KEY);
    updateCurrentDateLabel();
    updateDateArrowState();

    const today = getTodayDateString();

    window.dispatchEvent(
        new CustomEvent("lunavis:date-changed", {
            detail: { date: today }
        })
    );
}

/* -------------------------
   DATE WINDOW LOGIC
-------------------------- */

function getDateOffsetFromAnchor(dateString) {
    const [ay, am, ad] = loadAnchorDate().split("-").map(Number);
    const [cy, cm, cd] = dateString.split("-").map(Number);

    const anchor = new Date(Date.UTC(ay, am - 1, ad));
    const current = new Date(Date.UTC(cy, cm - 1, cd));

    const diffMs = current - anchor;
    return Math.round(diffMs / (1000 * 60 * 60 * 24));
}

function canMoveDateBy(days) {
    const current = loadSelectedDate();
    const currentOffset = getDateOffsetFromAnchor(current);
    const nextOffset = currentOffset + days;

    return nextOffset >= -DATE_WINDOW_DAYS && nextOffset <= DATE_WINDOW_DAYS;
}

function updateDateArrowState() {
    const prevBtn = document.getElementById("prev-date-btn");
    const nextBtn = document.getElementById("next-date-btn");

    if (prevBtn) prevBtn.disabled = !canMoveDateBy(-1);
    if (nextBtn) nextBtn.disabled = !canMoveDateBy(1);
}

/* -------------------------
   NAV LABEL
-------------------------- */

function updateCurrentDateLabel() {
    const label = document.getElementById("current-date-label");
    if (!label) return;

    const stored = localStorage.getItem(DATE_STORAGE_KEY);
    label.textContent = stored ? "Change Date" : "Set Date";
}

/* -------------------------
   PANEL OPEN/CLOSE
-------------------------- */

function openDatePanel() {
    const panel = document.getElementById("date-panel");
    if (!panel) return;

    populateGlobalDateFields();
    panel.classList.remove("hidden");
}

function closeDatePanel() {
    const panel = document.getElementById("date-panel");
    if (!panel) return;

    panel.classList.add("hidden");
}

/* -------------------------
   PANEL FIELDS
-------------------------- */

function populateGlobalDateFields() {
    const dateInput = document.getElementById("global-date-input");
    const display = document.getElementById("global-date-display");

    const selectedDate = loadSelectedDate();

    if (dateInput) dateInput.value = selectedDate;

    if (display) {
        display.textContent = `Current date: ${formatDateLong(selectedDate)}`;
    }
}

/* -------------------------
   DATE ACTIONS
-------------------------- */

function handleGlobalDateChange() {
    const dateInput = document.getElementById("global-date-input");
    const display = document.getElementById("global-date-display");

    const value = dateInput?.value;
    if (!value) {
        if (display) display.textContent = "Please choose a date.";
        return;
    }

    setSelectedDateAndAnchor(value);
    populateGlobalDateFields();
    closeDatePanel();
}

function setDateToToday() {
    const today = getTodayDateString();
    setSelectedDateAndAnchor(today);
    populateGlobalDateFields();
}

function clearGlobalDateFields() {
    clearSelectedDate();
    populateGlobalDateFields();
    updateDateArrowState();
}

function changeDateByDays(days) {
    if (!canMoveDateBy(days)) {
        return;
    }

    const [year, month, day] = loadSelectedDate().split("-").map(Number);
    const date = new Date(Date.UTC(year, month - 1, day));
    date.setUTCDate(date.getUTCDate() + days);

    const nextDate = date.toISOString().split("T")[0];
    saveSelectedDate(nextDate);
}

/* -------------------------
   PAGE FIELD SYNC
-------------------------- */

function applyStoredDateToPageFields() {
    const dateInput = document.getElementById("date");
    if (!dateInput) return false;

    dateInput.value = loadSelectedDate();
    updateDateArrowState();
    return true;
}

function renderSelectedDateSummary(elementId = "selected-date-summary") {
    const el = document.getElementById(elementId);
    if (!el) return;

    const date = loadSelectedDate();
    el.innerHTML = `<strong>Selected Date:</strong> ${formatDateLong(date)}`;
}

/* -------------------------
   INIT
-------------------------- */

function initializeGlobalDateUI() {
    updateCurrentDateLabel();
    populateGlobalDateFields();
    updateDateArrowState();

    const toggleBtn = document.getElementById("calendar-toggle-btn");
    const closeBtn = document.getElementById("close-date-panel-btn");
    const dateInput = document.getElementById("global-date-input");
    const todayBtn = document.getElementById("global-date-today-btn");
    const clearBtn = document.getElementById("global-date-clear-btn");

    if (toggleBtn) {
        toggleBtn.addEventListener("click", openDatePanel);
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", closeDatePanel);
    }

    if (dateInput) {
        dateInput.addEventListener("change", handleGlobalDateChange);
    }

    if (todayBtn) {
        todayBtn.addEventListener("click", setDateToToday);
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", clearGlobalDateFields);
    }
}