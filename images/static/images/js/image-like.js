"use strict";

(() => {
    const initializeImageLike = () => {
        const button = document.querySelector(
            "[data-like-button]"
        );

        if (!button) {
            return;
        }

        const buttonText = button.querySelector(
            "[data-like-button-text]"
        );

        const countElement = document.querySelector(
            "[data-like-count]"
        );

        const labelElement = document.querySelector(
            "[data-like-label]"
        );

        const errorElement = document.querySelector(
            "[data-like-error]"
        );

        if (
            !buttonText
            || !countElement
            || !labelElement
            || !errorElement
        ) {
            return;
        }

        const updateState = (
            action,
            count
        ) => {
            const liked =
                action === "unlike";

            button.dataset.action = action;

            button.classList.toggle(
                "is-liked",
                liked
            );

            button.setAttribute(
                "aria-pressed",
                String(liked)
            );

            buttonText.textContent =
                liked
                    ? "Unlike"
                    : "Like";

            countElement.textContent =
                String(count);

            labelElement.textContent =
                count === 1
                    ? "like"
                    : "likes";
        };

        button.addEventListener(
            "click",
            async () => {
                if (button.disabled) {
                    return;
                }

                const action =
                    button.dataset.action;

                if (
                    action !== "like"
                    && action !== "unlike"
                ) {
                    return;
                }

                const previousCount =
                    Math.max(
                        Number.parseInt(
                            countElement.textContent,
                            10
                        ) || 0,
                        0
                    );

                const nextAction =
                    action === "like"
                        ? "unlike"
                        : "like";

                const nextCount =
                    action === "like"
                        ? previousCount + 1
                        : Math.max(
                            previousCount - 1,
                            0
                        );

                const csrfToken =
                    window.getCSRFToken?.();

                if (!csrfToken) {
                    window.UI.showError(
                        errorElement,
                        "CSRF token could not be found."
                    );

                    return;
                }

                window.UI.hideError(
                    errorElement
                );

                window.UI.setButtonLoading(
                    button
                );

                updateState(
                    nextAction,
                    nextCount
                );

                try {
                    const formData =
                        new FormData();

                    formData.append(
                        "id",
                        button.dataset.imageId
                    );

                    formData.append(
                        "action",
                        action
                    );

                    const response =
                        await fetch(
                            button.dataset.likeUrl,
                            {
                                method: "POST",
                                headers: {
                                    "X-CSRFToken":
                                        csrfToken,
                                    "X-Requested-With":
                                        "XMLHttpRequest",
                                    "Accept":
                                        "application/json",
                                },
                                credentials:
                                    "same-origin",
                                body: formData,
                            }
                        );

                    const data =
                        await response.json();

                    if (
                        !response.ok
                        || data.status !== "ok"
                    ) {
                        throw new Error(
                            data.message
                            || "The like could not be updated."
                        );
                    }

                    if (!data.changed) {
                        updateState(
                            action,
                            previousCount
                        );
                    }
                } catch (error) {
                    updateState(
                        action,
                        previousCount
                    );

                    window.UI.showError(
                        errorElement,
                        error.message
                        || "The like could not be updated."
                    );
                } finally {
                    window.UI.setButtonLoading(
                        button,
                        {
                            loading: false,
                        }
                    );
                }
            }
        );
    };

    window.UI.initializeWhenReady(
        initializeImageLike
    );
})();
