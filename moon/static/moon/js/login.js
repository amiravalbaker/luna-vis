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
        status.textContent = `Error: ${error.message}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("login-form");
    if (form) {
        form.addEventListener("submit", handleLoginSubmit);
    }
});