const ACCESS_TOKEN_KEY = "lunavis_access_token";
const REFRESH_TOKEN_KEY = "lunavis_refresh_token";
const USER_KEY = "lunavis_user";
const AUTH_DATE_STORAGE_KEY = "lunavis_selected_date";
const AUTH_DATE_ANCHOR_KEY = "lunavis_anchor_date";


function resetSelectedDateToToday() {
    const today = new Date().toISOString().split("T")[0];

    if (typeof setSelectedDateAndAnchor === "function") {
        setSelectedDateAndAnchor(today);
        return;
    }

    localStorage.setItem(AUTH_DATE_STORAGE_KEY, today);
    localStorage.setItem(AUTH_DATE_ANCHOR_KEY, today);
}

function saveTokens(access, refresh) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

function getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function hasRefreshSession() {
    return !!getRefreshToken();
}

function clearAuth() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

function saveCurrentUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function getCurrentUser() {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;

    try {
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

function isLoggedIn() {
    return !!getAccessToken() || hasRefreshSession() || !!getCurrentUser();
}

async function authenticatedApiGet(url) {
    let token = getAccessToken();
    if (!token) {
        if (hasRefreshSession()) {
            token = await refreshAccessToken();
        } else {
            throw new Error("Not logged in.");
        }
    }

    try {
        return await apiGet(url, token);
    } catch (error) {
        if (String(error.message).includes("token_not_valid")) {
            token = await refreshAccessToken();
            return await apiGet(url, token);
        }
        throw error;
    }
}

async function apiPost(url, body, token = null) {
    const headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
    });

    const contentType = response.headers.get("content-type") || "";
    const data = contentType.includes("application/json")
        ? await response.json()
        : await response.text();

    if (!response.ok) {
        throw new Error(typeof data === "string" ? data : JSON.stringify(data));
    }

    return data;
}

async function authenticatedApiPost(url, body) {
    let token = getAccessToken();
    if (!token) {
        if (hasRefreshSession()) {
            token = await refreshAccessToken();
        } else {
            throw new Error("Not logged in.");
        }
    }

    try {
        return await apiPost(url, body, token);
    } catch (error) {
        if (String(error.message).includes("token_not_valid")) {
            token = await refreshAccessToken();
            return await apiPost(url, body, token);
        }
        throw error;
    }
}

async function apiDelete(url, token = null) {
    const headers = {
        "Accept": "application/json",
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        method: "DELETE",
        headers,
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Delete failed.");
    }

    return true;
}

async function authenticatedApiDelete(url) {
    let token = getAccessToken();
    if (!token) {
        if (hasRefreshSession()) {
            token = await refreshAccessToken();
        } else {
            throw new Error("Not logged in.");
        }
    }

    try {
        return await apiDelete(url, token);
    } catch (error) {
        if (String(error.message).includes("token_not_valid")) {
            token = await refreshAccessToken();
            return await apiDelete(url, token);
        }
        throw error;
    }
}

async function loginUser(username, password) {
    const data = await apiPost("/api/token/", {
        username,
        password,
    });

    saveTokens(data.access, data.refresh);

    const me = await authenticatedApiGet("/api/v1/me/");
    saveCurrentUser(me);
    resetSelectedDateToToday();

    return me;
}

async function registerUser(username, email, password, password_confirm) {
    const data = await apiPost("/api/v1/register/", {
        username,
        email,
        password,
        password_confirm,
    });

    saveTokens(data.access, data.refresh);
    saveCurrentUser(data.user);
    resetSelectedDateToToday();

    return data.user;
}

async function refreshAccessToken() {
    const refresh = getRefreshToken();
    if (!refresh) {
        clearAuth();
        throw new Error("Session expired. Please log in again.");
    }

    try {
        const data = await apiPost("/api/token/refresh/", { refresh });
        localStorage.setItem(ACCESS_TOKEN_KEY, data.access);
        return data.access;
    } catch (error) {
        clearAuth();
        throw new Error("Session expired. Please log in again.");
    }
}

async function loadCurrentUserFromApi() {
    const me = await authenticatedApiGet("/api/v1/me/");
    saveCurrentUser(me);
    return me;
}

function logoutUser() {
    clearAuth();
    window.location.href = "/";
}

function updateAuthNav() {
    const authNav = document.getElementById("auth-nav");
    if (!authNav) return;

    const user = getCurrentUser();

    if (user) {
        authNav.innerHTML = `
            <span class="nav-user">Hi, ${user.username}</span>
            <a href="/favourites/">Favourites</a>
            <a href="/observations/">Observations</a>
            <button id="logout-btn" class="link-button">Logout</button>
        `;

        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", logoutUser);
        }
    } else {
        authNav.innerHTML = `
            <a href="/login/">Login</a>
            <a href="/register/">Register</a>
        `;
    }
}

function updateAuthPanel() {
    const panel = document.getElementById("auth-nav-panel");
    if (!panel) return;

    const user = getCurrentUser();

    if (user) {
        panel.innerHTML = `
            <div><strong>Signed in as:</strong> ${user.username}</div>
            <button id="settings-test-email-btn" class="link-button" type="button">Send test email</button>
            <div id="settings-test-email-status"></div>
            <button id="settings-logout-btn" class="link-button" type="button">Logout</button>
        `;

        document.getElementById("settings-test-email-btn")?.addEventListener("click", async () => {
            const statusEl = document.getElementById("settings-test-email-status");
            if (statusEl) statusEl.textContent = "Sending test email...";

            try {
                const data = await authenticatedApiPost("/api/v1/auth/test-email/", {});
                if (statusEl) statusEl.textContent = data.detail || "Test email sent.";
            } catch (error) {
                if (statusEl) statusEl.textContent = `Error: ${error.message}`;
            }
        });

        document.getElementById("settings-logout-btn")?.addEventListener("click", logoutUser);
    } else {
        panel.innerHTML = `
            <div class="settings-link-list">
                <a href="/login/">Login</a>
                <a href="/register/">Register</a>
            </div>
        `;
    }
}