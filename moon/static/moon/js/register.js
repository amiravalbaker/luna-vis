async function handleRegisterSubmit(event) {
    event.preventDefault();

    const status = document.getElementById("register-status");
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const password_confirm = document.getElementById("password_confirm").value;

    status.textContent = "Creating account...";

    try {
        await registerUser(username, email, password, password_confirm);
        status.textContent = "Registration successful.";
        window.location.href = "/";
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("register-form");
    if (form) {
        form.addEventListener("submit", handleRegisterSubmit);
    }
});