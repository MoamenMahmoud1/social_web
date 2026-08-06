"use strict";

(() => {
    const getSafeCount = (element) => {
        const count = Number.parseInt(
            element.textContent.trim(),
            10
        );

        if (
            Number.isNaN(count)
            || count < 0
        ) {
            return 0;
        }

        return count;
    };

    const updateLikeLabel = (
        labelElement,
        count
    ) => {
        labelElement.textContent =
            count === 1
                ? "like"
                : "likes";
    };

    const applyLikeState = ({
        button,
        buttonText,
        countElement,
        labelElement,
        nextAction,
        count,
    }) => {
        const userHasLiked =
            nextAction === "unlike";

        countElement.textContent =
            String(count);

        updateLikeLabel(
            labelElement,
            count
        );

        button.dataset.action =
            nextAction;

        button.setAttribute(
            "aria-pressed",
            String(userHasLiked)
        );

        button.classList.toggle(
            "is-liked",
            userHasLiked
        );

        buttonText.textContent =
            userHasLiked
                ? "Unlike"
                : "Like";
    };

    const setLoadingState = (
        button,
        isLoading
    ) => {
        button.disabled = isLoading;

        button.classList.toggle(
            "is-loading",
            isLoading
        );

        button.setAttribute(
            "aria-busy",
            String(isLoading)
        );
    };

    const getCSRFToken = () => {
        if (
            typeof window.getCSRFToken
            !== "function"
        ) {
            return null;
        }

        return window.getCSRFToken();
    };

    const sendLikeRequest = async ({
        url,
        imageId,
        action,
    }) => {
        const csrfToken =
            getCSRFToken();

        if (!csrfToken) {
            throw new Error(
                "CSRF token could not be found."
            );
        }

        const formData = new FormData();

        formData.append(
            "id",
            imageId
        );

        formData.append(
            "action",
            action
        );

        const response = await fetch(
            url,
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
                mode: "same-origin",
                credentials: "same-origin",
                body: formData,
            }
        );

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error(
                "The server returned an invalid response."
            );
        }

        if (
            !response.ok
            || data.status !== "ok"
        ) {
            throw new Error(
                data.message
                || `The like request failed with status ${response.status}.`
            );
        }

        return data;
    };

    const initializeImageLike = () => {
        const button =
            document.querySelector(
                "[data-like-button]"
            );

        if (!button) {
            return;
        }

        const buttonText =
            button.querySelector(
                "[data-like-button-text]"
            );

        const countElement =
            document.querySelector(
                "[data-like-count]"
            );

        const labelElement =
            document.querySelector(
                "[data-like-label]"
            );

        const errorElement =
            document.querySelector(
                "[data-like-error]"
            );

        if (
            !buttonText
            || !countElement
            || !labelElement
            || !errorElement
        ) {
            console.error(
                "The like interface is incomplete."
            );

            return;
        }

        const likeUrl =
            button.dataset.likeUrl;

        const imageId =
            button.dataset.imageId;

        if (
            !likeUrl
            || !imageId
        ) {
            console.error(
                "Like button data is incomplete."
            );

            return;
        }

        let requestInProgress = false;

        button.classList.toggle(
            "is-liked",
            button.dataset.action === "unlike"
        );

        button.addEventListener(
            "click",
            async () => {
                if (requestInProgress) {
                    return;
                }

                const previousAction =
                    button.dataset.action;

                if (
                    previousAction !== "like"
                    && previousAction !== "unlike"
                ) {
                    console.error(
                        "The like action is invalid."
                    );

                    return;
                }

                const previousCount =
                    getSafeCount(
                        countElement
                    );

                const optimisticCount =
                    previousAction === "like"
                        ? previousCount + 1
                        : Math.max(
                            previousCount - 1,
                            0
                        );

                const optimisticNextAction =
                    previousAction === "like"
                        ? "unlike"
                        : "like";

                requestInProgress = true;
                errorElement.hidden = true;

                setLoadingState(
                    button,
                    true
                );

                applyLikeState({
                    button,
                    buttonText,
                    countElement,
                    labelElement,
                    nextAction:
                        optimisticNextAction,
                    count:
                        optimisticCount,
                });

                try {
                    const data =
                        await sendLikeRequest({
                            url: likeUrl,
                            imageId,
                            action:
                                previousAction,
                        });

                    if (!data.changed) {
                        applyLikeState({
                            button,
                            buttonText,
                            countElement,
                            labelElement,
                            nextAction:
                                previousAction,
                            count:
                                previousCount,
                        });
                    }
                } catch (error) {
                    applyLikeState({
                        button,
                        buttonText,
                        countElement,
                        labelElement,
                        nextAction:
                            previousAction,
                        count:
                            previousCount,
                    });

                    errorElement.textContent =
                        error.message
                        || "The like could not be updated.";

                    errorElement.hidden =
                        false;

                    console.error(
                        "Could not update image like:",
                        error
                    );
                } finally {
                    requestInProgress = false;

                    setLoadingState(
                        button,
                        false
                    );
                }
            }
        );
    };

    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializeImageLike,
            {
                once: true,
            }
        );
    } else {
        initializeImageLike();
    }
})();

