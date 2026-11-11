console.log("app loaded");


// Ingredient filters: pressing Enter in an ingredient box asks the server for
// the closest real ingredient and turns it into a removable chip. Each chip
// holds a hidden input, so it is sent with the form.
async function addChip(input) {
    const typed = input.value.trim();
    if (!typed) return;

    const message = input.parentElement.querySelector(".chip-message");
    const response = await fetch(input.dataset.matchUrl + "?name=" + encodeURIComponent(typed));
    const { name } = await response.json();
    input.value = "";

    if (!name) {
        message.textContent = `No ingredient called "${typed}".`;
        return;
    }
    message.textContent = name === typed.toLowerCase() ? "" : `Using "${name}" (you typed "${typed}").`;

    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = name;

    const hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.name = input.dataset.chipName;
    hidden.value = name;

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "chip-remove";
    remove.setAttribute("aria-label", "Remove " + name);
    remove.textContent = "×";

    chip.append(hidden, remove);
    input.parentElement.querySelector(".chips").append(chip);
}

document.querySelectorAll("[data-chip-name]").forEach((input) => {
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();  // add a chip instead of submitting the form
            addChip(input);
        }
    });
});

// Before submitting, turn any text typed but not entered yet into chips.
// Matching takes a moment, so the form waits for it and then submits.
const filterForm = document.querySelector("form:has([data-chip-name])");
if (filterForm) {
    filterForm.addEventListener("submit", async (event) => {
        const pending = [...filterForm.querySelectorAll("[data-chip-name]")].filter((input) => input.value.trim());
        if (pending.length === 0) return;
        event.preventDefault();
        for (const input of pending) {
            await addChip(input);
        }
        filterForm.submit();
    });
}

document.addEventListener("click", (event) => {
    if (event.target.classList.contains("chip-remove")) {
        event.target.closest(".chip").remove();
    }
});
