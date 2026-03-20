function extractErrorMessage(error) {
    const raw = String(error?.message || "").trim();
    if (!raw) return "Something went wrong.";

    try {
        const parsed = JSON.parse(raw);
        return parsed.detail || parsed.error || raw;
    } catch {
        return raw;
    }
}

async function handleLoginSubmit(event) {
    event.preventDefault();

    const status = document.getElementById("login-status");
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    status.textContent = "Logging in...";

    try {
        await loginUser(username, password);
        status.textContent = "Login successful.";
        window.location.href = "/";
    } catch (error) {
        status.textContent = `Error: ${extractErrorMessage(error)}`;
    }
}

async function handleResendVerificationClick() {
    const emailInput = document.getElementById("verification-email");
    const status = document.getElementById("verification-status");
    const email = emailInput?.value?.trim();

    if (!email) {
        if (status) status.textContent = "Enter your email address first.";
        return;
    }

    if (status) status.textContent = "Sending verification email...";

    try {
        const data = await apiPost("/api/v1/auth/resend-verification-email/", { email });
        if (status) status.textContent = data.detail || "Verification email sent.";
    } catch (error) {
        if (status) status.textContent = `Error: ${extractErrorMessage(error)}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    if (form) {
        form.addEventListener("submit", handleLoginSubmit);
    }

    document
        .getElementById("resend-verification-btn")
        ?.addEventListener("click", handleResendVerificationClick);
});