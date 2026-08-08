"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(
        "[data-delete-form]"
    );

    if (!form) {
        return;
    }

    form.addEventListener("submit", (event) => {
        const confirmed = window.confirm(
            "Are you sure you want to delete this image?"
        );

        if (!confirmed) {
            event.preventDefault();
            return;
        }

        const button = form.querySelector(
            "button[type='submit']"
        );

        if (button) {
            button.disabled = true;
        }
    });
});
