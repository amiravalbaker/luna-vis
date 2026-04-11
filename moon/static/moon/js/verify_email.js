function parseApiError(error) {
    const raw = String(error?.message || "").trim();
    if (!raw) return "Something went wrong.";

    try {
        const parsed = JSON.parse(raw);
        return parsed.detail || parsed.error || raw;
    } catch {
        return raw;
    }
}

async function verifyEmailFromUrl() {
    const statusEl = document.getElementById("verify-email-status");
    if (!statusEl) return;

    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
        statusEl.textContent = "Verification token is missing. Please use the full link from your email.";
        return;
    }

    statusEl.textContent = "Verifying your email...";

    try {
        const data = await apiPost("/api/v1/auth/verify-email/", { token });
        statusEl.textContent = data.detail || "Verification successful. You can now log in to your app.";
    } catch (error) {
        statusEl.textContent = `Error: ${parseApiError(error)}`;
    }
}

document.addEventListener("DOMContentLoaded", verifyEmailFromUrl);
