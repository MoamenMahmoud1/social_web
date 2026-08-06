"use strict";

(() => {
    const STORAGE_KEY = "bookmarks-theme";
    const rootElement = document.documentElement;

    const getSystemTheme = () => {
        return window.matchMedia(
            "(prefers-color-scheme: dark)"
        ).matches
            ? "dark"
            : "light";
    };

    let selectedTheme = getSystemTheme();

    try {
        const storedTheme = localStorage.getItem(
            STORAGE_KEY
        );

        if (
            storedTheme === "light"
            || storedTheme === "dark"
        ) {
            selectedTheme = storedTheme;
        }
    } catch (error) {
        // Use the system theme when storage is unavailable.
    }

    rootElement.setAttribute(
        "data-bs-theme",
        selectedTheme
    );
})();