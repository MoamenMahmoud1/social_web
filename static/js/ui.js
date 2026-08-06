"use strict";

(() => {
    const getElementText = (element) => {
        if (!element) {
            return "";
        }

        return element.textContent.trim();
    };

    const setButtonLoading = (
        button,
        {
            loading = true,
            loadingText = null,
        } = {}
    ) => {
        if (!button) {
            return;
        }

        if (loading) {
            if (
                !button.dataset.originalText
            ) {
                button.dataset.originalText =
                    getElementText(button);
            }

            button.disabled = true;

            button.classList.add(
                "is-loading"
            );

            button.setAttribute(
                "aria-busy",
                "true"
            );

            if (loadingText) {
                button.textContent =
                    loadingText;
            }

            return;
        }

        button.disabled = false;

        button.classList.remove(
            "is-loading"
        );

        button.removeAttribute(
            "aria-busy"
        );

        if (
            loadingText
            && button.dataset.originalText
        ) {
            button.textContent =
                button.dataset.originalText;
        }

        delete button.dataset.originalText;
    };

    const hideError = (
        errorElement
    ) => {
        if (!errorElement) {
            return;
        }

        errorElement.hidden = true;
    };

    const showError = (
        errorElement,
        message
    ) => {
        if (!errorElement) {
            return;
        }

        errorElement.textContent =
            message;

        errorElement.hidden = false;
    };

    const initializeWhenReady = (
        callback
    ) => {
        if (
            typeof callback
            !== "function"
        ) {
            return;
        }

        if (
            document.readyState
            === "loading"
        ) {
            document.addEventListener(
                "DOMContentLoaded",
                callback,
                {
                    once: true,
                }
            );

            return;
        }

        callback();
    };

    window.UI = Object.freeze({
        setButtonLoading,
        hideError,
        showError,
        initializeWhenReady,
    });
})();

