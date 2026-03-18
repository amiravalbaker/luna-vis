function requireLoginOrRedirect() {
    if (!isLoggedIn()) {
        window.location.href = "/login/";
        return false;
    }
    return true;
}

async function loadFavourites() {
    const container = document.getElementById("favourites-list");

    try {
        const token = getAccessToken();
        const data = await apiGet("/api/v1/favourites/", token);

        if (!data.length) {
            container.innerHTML = "<p>No favourite locations saved yet.</p>";
            return;
        }

        container.innerHTML = data.map(fav => `
            <div class="card">
                <h3>${fav.name}</h3>
                <div><strong>Coordinates:</strong> ${fav.latitude.toFixed(4)}, ${fav.longitude.toFixed(4)}</div>
                <div><strong>Elevation:</strong> ${fav.elevation_m} m</div>
                <div class="button-row">
                    <button type="button" class="use-favourite-btn" data-id="${fav.id}"
                        data-name="${fav.name}"
                        data-lat="${fav.latitude}"
                        data-lon="${fav.longitude}"
                        data-elevation="${fav.elevation_m}">
                        Use this location
                    </button>
                    <button type="button" class="delete-favourite-btn" data-id="${fav.id}">
                        Delete
                    </button>
                </div>
            </div>
        `).join("");

        document.querySelectorAll(".delete-favourite-btn").forEach(btn => {
            btn.addEventListener("click", async () => {
                await deleteFavourite(btn.dataset.id);
            });
        });

        document.querySelectorAll(".use-favourite-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const locationData = {
                    display_name: btn.dataset.name,
                    lat: parseFloat(btn.dataset.lat),
                    lon: parseFloat(btn.dataset.lon),
                    elevation_m: parseInt(btn.dataset.elevation, 10),
                    tz: document.getElementById("tz")?.value || Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
                };

                saveSelectedLocation(locationData);
                document.getElementById("favourite-status").textContent = `"${locationData.display_name}" selected as current location.`;
            });
        });
    } catch (error) {
        container.innerHTML = `<p>Error loading favourites: ${error.message}</p>`;
    }
}

async function deleteFavourite(id) {
    const token = getAccessToken();
    try {
        await apiDelete(`/api/v1/favourites/${id}/`, token);
        document.getElementById("favourite-status").textContent = "Favourite deleted.";
        await loadFavourites();
    } catch (error) {
        document.getElementById("favourite-status").textContent = `Error: ${error.message}`;
    }
}

async function handleFavouriteSubmit(event) {
    event.preventDefault();

    const status = document.getElementById("favourite-status");
    const name = document.getElementById("name").value.trim();
    const lat = document.getElementById("lat").value;
    const lon = document.getElementById("lon").value;
    const elevation_m = document.getElementById("elevation_m").value || 0;

    if (!name || !lat || !lon) {
        status.textContent = "Please provide a name and choose a location first.";
        return;
    }

    status.textContent = "Saving favourite...";

    try {
        const token = getAccessToken();
        await apiPost("/api/v1/favourites/", {
            name,
            latitude: parseFloat(lat),
            longitude: parseFloat(lon),
            elevation_m: parseInt(elevation_m, 10),
        }, token);

        status.textContent = "Favourite saved.";
        document.getElementById("favourite-form").reset();
        document.getElementById("location-display").textContent = "";
        await loadFavourites();
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!requireLoginOrRedirect()) return;

    applyStoredLocationToFields();
    loadFavourites();
    renderSelectedLocationSummary();

    document.getElementById("favourite-form").addEventListener("submit", handleFavouriteSubmit);
    document.getElementById("find-location-btn").addEventListener("click", handleFindPlaceShared);
    document.getElementById("use-my-location-btn").addEventListener("click", handleUseMyLocationShared);
});