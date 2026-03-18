console.log("location.js loaded");

const LOCATION_STORAGE_KEY = "lunavis_selected_location";

/* -------------------------
   STORAGE
-------------------------- */

function saveSelectedLocation(locationData) {
    localStorage.setItem(LOCATION_STORAGE_KEY, JSON.stringify(locationData));
    updateCurrentLocationLabel();

    window.dispatchEvent(
        new CustomEvent("lunavis:location-changed", {
            detail: locationData
        })
    );
}

function loadSelectedLocation() {
    const raw = localStorage.getItem(LOCATION_STORAGE_KEY);
    if (!raw) return null;

    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

function clearSelectedLocation() {
    localStorage.removeItem(LOCATION_STORAGE_KEY);
    updateCurrentLocationLabel();

    window.dispatchEvent(
        new CustomEvent("lunavis:location-changed", {
            detail: null
        })
    );
}

/* -------------------------
   NAV LABEL
-------------------------- */

function updateCurrentLocationLabel() {
    const label = document.getElementById("current-location-label");
    if (!label) return;

    const location = loadSelectedLocation();
    label.textContent = location ? "Change Location" : "Set Location";
}

/* -------------------------
   GEOCODING / GEOLOCATION
-------------------------- */

async function geocodePlace(placeName) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(placeName)}&limit=1`;

    const response = await fetch(url, {
        headers: { "Accept": "application/json" }
    });

    if (!response.ok) {
        throw new Error("Failed to geocode place.");
    }

    const results = await response.json();
    if (!results.length) {
        throw new Error("No matching place found.");
    }

    const result = results[0];

    return {
        display_name: result.display_name,
        lat: parseFloat(result.lat),
        lon: parseFloat(result.lon),
        elevation_m: 0,
        tz: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    };
}

async function reverseGeocode(lat, lon) {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`;

    const response = await fetch(url, {
        headers: { "Accept": "application/json" }
    });

    if (!response.ok) {
        throw new Error("Failed to reverse geocode location.");
    }

    const result = await response.json();

    return {
        display_name: result.display_name || `${lat.toFixed(4)}, ${lon.toFixed(4)}`,
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        elevation_m: 0,
        tz: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
    };
}

function getCurrentBrowserLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Geolocation is not supported by your browser."));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;

                try {
                    const locationData = await reverseGeocode(lat, lon);
                    resolve(locationData);
                } catch {
                    resolve({
                        display_name: `${lat.toFixed(4)}, ${lon.toFixed(4)}`,
                        lat,
                        lon,
                        elevation_m: 0,
                        tz: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
                    });
                }
            },
            (error) => reject(new Error(error.message))
        );
    });
}

async function fetchLocationMeta(lat, lon) {
    const params = new URLSearchParams({ lat, lon });
    return await apiGet(`/api/v1/location-meta/?${params.toString()}`);
}

/* -------------------------
   PANEL OPEN/CLOSE
-------------------------- */

function openLocationPanel() {
    const panel = document.getElementById("location-panel");
    if (!panel) {
        console.error("location-panel not found");
        return;
    }

    populateGlobalLocationFields();
    panel.classList.remove("hidden");
    loadFavouriteLocationsIntoPanel();
}

function closeLocationPanel() {
    const panel = document.getElementById("location-panel");
    if (!panel) return;

    panel.classList.add("hidden");
}

/* -------------------------
   PANEL FIELDS
-------------------------- */

function populateGlobalLocationFields() {
    const location = loadSelectedLocation();

    const input = document.getElementById("global-location-input");
    const tzInput = document.getElementById("global-tz-input");
    const elevationInput = document.getElementById("global-elevation-input");
    const display = document.getElementById("global-location-display");

    if (!input || !tzInput || !elevationInput || !display) return;

    if (location) {
        input.value = location.display_name || "";
        tzInput.value = location.tz_label || location.tz || "UTC";
        elevationInput.value = location.elevation_m ?? 0;
        display.textContent = `Current location: ${location.display_name} | ${location.tz_label || location.tz || "UTC"} | ${location.elevation_m ?? 0} m`;
    } else {
        input.value = "";
        tzInput.value = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
        elevationInput.value = 0;
        display.textContent = "No location selected.";
    }

    const authSection = document.getElementById("location-auth-section");
    if (authSection) {
        authSection.classList.toggle("hidden", !isLoggedIn());
    }
}

function applyStoredLocationToPageFields() {
    const location = loadSelectedLocation();
    if (!location) return false;

    const tzInput = document.getElementById("tz");
    const elevationInput = document.getElementById("elevation_m");

    if (tzInput) tzInput.value = location.tz || "UTC";
    if (elevationInput) elevationInput.value = location.elevation_m ?? 0;

    return true;
}

function getSelectedLocationOrShowMessage(messageElementId = null) {
    const location = loadSelectedLocation();
    if (!location) {
        if (messageElementId) {
            const el = document.getElementById(messageElementId);
            if (el) {
                el.textContent = "Please set your location using the location icon in the top bar.";
            }
        }
        return null;
    }
    return location;
}

/* -------------------------
   LOCATION ACTIONS
-------------------------- */

async function handleGlobalFindPlace() {
    const input = document.getElementById("global-location-input");
    const display = document.getElementById("global-location-display");

    const placeName = input?.value.trim();
    if (!placeName) {
        if (display) display.textContent = "Please enter a place name.";
        return;
    }

    if (display) display.textContent = "Finding place...";

    try {
        const locationData = await geocodePlace(placeName);
        const meta = await fetchLocationMeta(locationData.lat, locationData.lon);

        locationData.tz = meta.tz;
        locationData.tz_label = meta.tz_label;
        locationData.elevation_m = meta.elevation_m;

        saveSelectedLocation(locationData);
        populateGlobalLocationFields();
    } catch (error) {
        if (display) display.textContent = `Error: ${error.message}`;
    }
}

async function handleGlobalUseMyLocation() {
    const display = document.getElementById("global-location-display");

    if (display) display.textContent = "Finding your location...";

    try {
        const locationData = await getCurrentBrowserLocation();
        const meta = await fetchLocationMeta(locationData.lat, locationData.lon);

        locationData.tz = meta.tz;
        locationData.tz_label = meta.tz_label;
        locationData.elevation_m = meta.elevation_m;

        saveSelectedLocation(locationData);
        populateGlobalLocationFields();
    } catch (error) {
        if (display) display.textContent = `Error: ${error.message}`;
    }
}

function clearGlobalLocationFields() {
    clearSelectedLocation();

    const input = document.getElementById("global-location-input");
    const tzInput = document.getElementById("global-tz-input");
    const elevationInput = document.getElementById("global-elevation-input");
    const display = document.getElementById("global-location-display");

    if (input) input.value = "";
    if (tzInput) tzInput.value = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
    if (elevationInput) elevationInput.value = 0;
    if (display) display.textContent = "No location selected.";
}

/* -------------------------
   FAVOURITES
-------------------------- */

async function saveCurrentLocationAsFavouriteFromPanel() {
    const display = document.getElementById("global-location-display");

    if (!isLoggedIn()) {
        window.location.href = "/login/";
        return;
    }

    const location = loadSelectedLocation();
    if (!location) {
        if (display) display.textContent = "Please choose a location first.";
        return;
    }

    const name = prompt(
        "Enter a name for this favourite location:",
        location.display_name || "Saved Location"
    );
    if (!name) return;

    try {
        await authenticatedApiPost("/api/v1/favourites/", {
            name,
            latitude: parseFloat(location.lat),
            longitude: parseFloat(location.lon),
            elevation_m: parseInt(location.elevation_m || 0, 10),
        });

        if (display) display.textContent = `Saved "${name}" to favourites.`;
        await loadFavouriteLocationsIntoPanel();
    } catch (error) {
        if (display) display.textContent = `Error: ${error.message}`;
    }
}

async function loadFavouriteLocationsIntoPanel() {
    const container = document.getElementById("location-favourites-list");
    if (!container) return;

    if (!isLoggedIn()) {
        container.innerHTML = "";
        return;
    }

    try {
        const favourites = await authenticatedApiGet("/api/v1/favourites/");

        if (!favourites.length) {
            container.innerHTML = "<p>No saved favourites yet.</p>";
            return;
        }

        container.innerHTML = favourites.map(fav => `
            <div class="card">
                <div><strong>${fav.name}</strong></div>
                <div>${fav.latitude.toFixed(4)}, ${fav.longitude.toFixed(4)}</div>
                <div>${fav.elevation_m} m</div>
                <div class="button-row">
                    <button
                        type="button"
                        class="choose-favourite-btn"
                        data-name="${fav.name}"
                        data-lat="${fav.latitude}"
                        data-lon="${fav.longitude}"
                        data-elevation="${fav.elevation_m}">
                        Use
                    </button>
                </div>
            </div>
        `).join("");

        document.querySelectorAll(".choose-favourite-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                const lat = parseFloat(btn.dataset.lat);
                const lon = parseFloat(btn.dataset.lon);
                const elevation_m = parseInt(btn.dataset.elevation, 10);

                try {
                    const meta = await fetchLocationMeta(lat, lon);

                    const locationData = {
                        display_name: btn.dataset.name,
                        lat,
                        lon,
                        elevation_m,
                        tz: meta.tz,
                        tz_label: meta.tz_label,
                    };

                    saveSelectedLocation(locationData);
                    populateGlobalLocationFields();
                    closeLocationPanel();
                } catch (error) {
                    const display = document.getElementById("global-location-display");
                    if (display) display.textContent = `Error: ${error.message}`;
                }
            });
        });
    } catch (error) {
        container.innerHTML = `<p>Error loading favourites: ${error.message}</p>`;
    }
}

/* -------------------------
   PAGE SUMMARY
-------------------------- */

function renderSelectedLocationSummary(elementId = "selected-location-summary") {
    const el = document.getElementById(elementId);
    if (!el) return;

    const location = loadSelectedLocation();
    if (!location) {
        el.innerHTML = `<strong>Location:</strong> Not set`;
        return;
    }

    el.innerHTML = `
        <div><strong>Location:</strong> ${location.display_name}</div>
        <div><strong>Timezone:</strong> ${location.tz_label || location.tz || "N/A"}</div>
        <div><strong>Elevation:</strong> ${location.elevation_m ?? 0} m</div>
    `;
}

/* -------------------------
   INIT
-------------------------- */

function initializeGlobalLocationUI() {
    updateCurrentLocationLabel();
    populateGlobalLocationFields();

    const toggleBtn = document.getElementById("location-toggle-btn");
    const closeBtn = document.getElementById("close-location-panel-btn");
    const findBtn = document.getElementById("global-find-location-btn");
    const useMyLocationBtn = document.getElementById("global-use-my-location-btn");
    const clearBtn = document.getElementById("global-clear-location-btn");
    const saveFavBtn = document.getElementById("save-location-favourite-btn");

    if (toggleBtn) {
        toggleBtn.addEventListener("click", openLocationPanel);
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", closeLocationPanel);
    }

    if (findBtn) {
        findBtn.addEventListener("click", handleGlobalFindPlace);
    }

    if (useMyLocationBtn) {
        useMyLocationBtn.addEventListener("click", handleGlobalUseMyLocation);
    }

    if (clearBtn) {
        clearBtn.addEventListener("click", clearGlobalLocationFields);
    }

    if (saveFavBtn) {
        saveFavBtn.addEventListener("click", saveCurrentLocationAsFavouriteFromPanel);
    }
}