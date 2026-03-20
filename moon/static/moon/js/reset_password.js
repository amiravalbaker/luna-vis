function extractResetErrorMessage(error) {
    const raw = String(error?.message || "").trim();
    if (!raw) return "Something went wrong.";

    try {
        const parsed = JSON.parse(raw);
        if (typeof parsed === "string") return parsed;
        if (parsed.detail) return parsed.detail;
        if (parsed.error) return parsed.error;

        const firstField = Object.keys(parsed)[0];
        if (firstField && Array.isArray(parsed[firstField]) && parsed[firstField].length) {
            return parsed[firstField][0];
        }

        return raw;
    } catch {
        return raw;
    }
}

function getResetToken() {
    return new URLSearchParams(window.location.search).get("token");
}

async function handleResetPasswordSubmit(event) {
    event.preventDefault();

    const status = document.getElementById("reset-password-status");
    const token = getResetToken();
    const password = document.getElementById("new-password")?.value || "";
    const passwordConfirm = document.getElementById("new-password-confirm")?.value || "";

    if (!token) {
        status.textContent = "Reset token is missing. Please use the full link from your email.";
        return;
    }

    status.textContent = "Resetting password...";

    try {
        const data = await apiPost("/api/v1/auth/password-reset-confirm/", {
            token,
            password,
            password_confirm: passwordConfirm,
        });

        status.textContent = data.detail || "Password reset successful. You can now log in.";
        setTimeout(() => {
            window.location.href = "/login/";
        }, 1200);
    } catch (error) {
        status.textContent = `Error: ${extractResetErrorMessage(error)}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const status = document.getElementById("reset-password-status");
    if (status && !getResetToken()) {
        status.textContent = "Reset token is missing. Please use the full link from your email.";
    }

    document
        .getElementById("reset-password-form")
        ?.addEventListener("submit", handleResetPasswordSubmit);
});
