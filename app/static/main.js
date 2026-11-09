function showFavorite(button, isFavorite) {
    button.classList.toggle("is-favorite", isFavorite);
    button.setAttribute("aria-pressed", isFavorite ? "true" : "false");
    button.textContent = isFavorite ? button.dataset.onText : button.dataset.offText;
    const label = isFavorite ? button.dataset.onLabel : button.dataset.offLabel;
    if (label) {
        button.setAttribute("aria-label", label);
    }
}

document.querySelectorAll("form.js-favorite").forEach(function (form) {
    form.addEventListener("submit", async function (event) {
        event.preventDefault();
        const button = form.querySelector("button");
        const wasFavorite = button.getAttribute("aria-pressed") === "true";
        showFavorite(button, !wasFavorite);
        button.disabled = true;
        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: { "Accept": "application/json" },
            });
            if (!response.ok) {
                throw new Error(response.status);
            }
            const data = await response.json();
            showFavorite(button, data.favorite);
        } catch (error) {
            form.submit();
        } finally {
            button.disabled = false;
        }
    });
});
