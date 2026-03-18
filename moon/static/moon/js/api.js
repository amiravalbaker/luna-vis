async function apiGet(url, token = null) {
    const headers = {
        "Accept": "application/json"
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        method: "GET",
        headers: headers
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