"use strict";

(() => {
    const STORAGE_KEY = "bookmarks-theme";
    const LIGHT_THEME = "light";
    const DARK_THEME = "dark";

    const initializeThemeToggle = () => {
        const rootElement = document.documentElement;

        const toggleButtons = document.querySelectorAll(
            "[data-theme-toggle]"
        );

        if (toggleButtons.length === 0) {
            return;
        }

        const getCurrentTheme = () => {
            return rootElement.getAttribute(
                "data-bs-theme"
            ) === DARK_THEME
                ? DARK_THEME
                : LIGHT_THEME;
        };

        const updateButtons = (theme) => {
            const isDark = theme === DARK_THEME;

            toggleButtons.forEach((button) => {
                button.setAttribute(
                    "aria-pressed",
                    String(isDark)
                );

                button.setAttribute(
                    "aria-label",
                    isDark
                        ? "Switch to light mode"
                        : "Switch to dark mode"
                );
            });
        };

        const saveTheme = (theme) => {
            try {
                localStorage.setItem(
                    STORAGE_KEY,
                    theme
                );
            } catch (error) {
                // Theme switching still works without persistence.
            }
        };

        const applyTheme = (
            theme,
            shouldSave = true
        ) => {
            const normalizedTheme =
                theme === DARK_THEME
                    ? DARK_THEME
                    : LIGHT_THEME;

            rootElement.setAttribute(
                "data-bs-theme",
                normalizedTheme
            );

            updateButtons(normalizedTheme);

            if (shouldSave) {
                saveTheme(normalizedTheme);
            }
        };

        const toggleTheme = () => {
            const nextTheme =
                getCurrentTheme() === DARK_THEME
                    ? LIGHT_THEME
                    : DARK_THEME;

            applyTheme(nextTheme);
        };

        toggleButtons.forEach((button) => {
            button.addEventListener(
                "click",
                toggleTheme
            );
        });

        updateButtons(
            getCurrentTheme()
        );
    };

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeThemeToggle,
            {
                once: true,
            }
        );
    } else {
        initializeThemeToggle();
    }
})();