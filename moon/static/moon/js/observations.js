function requireLoginOrRedirect() {
    if (!isLoggedIn()) {
        window.location.href = "/login/";
        return false;
    }
    return true;
}

function setDefaultObservationTime() {
    const input = document.getElementById("observation_time");
    if (!input) return;

    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");

    const localValue = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
    input.value = localValue;
}

function toIsoUtc(localDateTimeString) {
    const date = new Date(localDateTimeString);
    return date.toISOString();
}

async function loadObservations() {
    const container = document.getElementById("observations-list");

    try {
        const token = getAccessToken();
        const data = await apiGet("/api/v1/observations/", token);

        if (!data.length) {
            container.innerHTML = "<p>No observations saved yet.</p>";
            return;
        }

        container.innerHTML = data.map(obs => `
            <div class="card">
                <h3>${obs.visible ? "Seen" : "Not Seen"}</h3>
                <div><strong>Time:</strong> ${obs.observation_time}</div>
                <div><strong>Location:</strong> ${obs.latitude.toFixed(4)}, ${obs.longitude.toFixed(4)}</div>
                <div><strong>Detection:</strong> ${obs.detection_method}</div>
                <div><strong>Sky:</strong> ${obs.sky_condition}</div>
                <div><strong>Notes:</strong> ${obs.notes || "None"}</div>

                ${obs.snapshot ? `
                    <div><strong>Moon Alt:</strong> ${obs.snapshot.moon_alt_deg?.toFixed(2)}°</div>
                    <div><strong>Moon Age:</strong> ${obs.snapshot.moon_age_hours?.toFixed(1)} h</div>
                ` : ""}

                ${obs.predictions?.length ? `
                    <div class="full-width">
                        <strong>Predictions:</strong>
                        <ul>
                            ${obs.predictions.map(p => `
                                <li>${p.model_name}: ${p.verdict} ${p.band ? `(${p.band})` : ""}</li>
                            `).join("")}
                        </ul>
                    </div>
                ` : ""}
            </div>
        `).join("");
    } catch (error) {
        container.innerHTML = `<p>Error loading observations: ${error.message}</p>`;
    }
}

async function handleObservationSubmit(event) {
    event.preventDefault();

    const status = document.getElementById("observation-status");
    const observer_name = document.getElementById("observer_name").value.trim();
    const lat = document.getElementById("lat").value;
    const lon = document.getElementById("lon").value;
    const elevation_m = document.getElementById("elevation_m").value || 0;
    const observation_time = document.getElementById("observation_time").value;
    const visible = document.getElementById("visible").value === "true";
    const detection_method = document.getElementById("detection_method").value;
    const sky_condition = document.getElementById("sky_condition").value;
    const time_spent_searching_minutes = document.getElementById("time_spent_searching_minutes").value || 0;
    const notes = document.getElementById("notes").value;
    const tz = document.getElementById("tz").value;

    if (!lat || !lon) {
        status.textContent = "Please choose a location first.";
        return;
    }

    status.textContent = "Saving observation...";

    try {
        const token = getAccessToken();

        await apiPost("/api/v1/observations/", {
            observer_name,
            latitude: parseFloat(lat),
            longitude: parseFloat(lon),
            elevation_m: parseInt(elevation_m, 10),
            sky_condition,
            observation_time: toIsoUtc(observation_time),
            time_spent_searching_minutes: parseInt(time_spent_searching_minutes, 10),
            visible,
            detection_method,
            notes,
            tz
        }, token);

        status.textContent = "Observation saved.";
        document.getElementById("observation-form").reset();
        setDefaultObservationTime();
        applyStoredLocationToFields();
        await loadObservations();
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!requireLoginOrRedirect()) return;

    applyStoredLocationToFields();
    setDefaultObservationTime();
    loadObservations();
    renderSelectedLocationSummary();

    document.getElementById("observation-form").addEventListener("submit", handleObservationSubmit);
    document.getElementById("find-location-btn").addEventListener("click", handleFindPlaceShared);
    document.getElementById("use-my-location-btn").addEventListener("click", handleUseMyLocationShared);
});