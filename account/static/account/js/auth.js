"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const content = document.querySelector(
        "[data-auth-content]"
    );

    if (!content) {
        return;
    }

    const updateHeight = () => {
        const activePanel = content.querySelector(
            ".tab-pane.active"
        );

        if (activePanel) {
            content.style.height =
                `${activePanel.scrollHeight}px`;
        }
    };

    document
        .querySelectorAll('[data-bs-toggle="pill"]')
        .forEach((tab) => {
            tab.addEventListener(
                "shown.bs.tab",
                updateHeight
            );
        });

    window.addEventListener(
        "resize",
        updateHeight
    );

    updateHeight();
});
