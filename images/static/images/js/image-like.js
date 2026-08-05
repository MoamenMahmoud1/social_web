"use strict";


function getSafeCount(element) {
    const count = Number.parseInt(
        element.textContent.trim(),
        10
    );

    if (Number.isNaN(count) || count < 0) {
        return 0;
    }

    return count;
}


function updateLikeLabel(labelElement, count) {
    labelElement.textContent = count === 1
        ? "like"
        : "likes";
}


function applyLikeState({
    button,
    buttonText,
    countElement,
    labelElement,
    action,
    count,
}) {
    const userHasLiked = action === "unlike";

    countElement.textContent = String(count);

    updateLikeLabel(
        labelElement,
        count
    );

    button.dataset.action = action;
    button.setAttribute(
        "aria-pressed",
        String(userHasLiked)
    );

    buttonText.textContent = userHasLiked
        ? "Unlike"
        : "Like";
}


async function sendLikeRequest({
    url,
    imageId,
    action,
    signal,
}) {
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
                "X-CSRFToken": window.csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
            mode: "same-origin",
            body: formData,
            signal,
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

    if (!response.ok || data.status !== "ok") {
        throw new Error(
            data.message || "The like request failed."
        );
    }

    return data;
}


function initializeImageLike() {
    const button = document.querySelector(
        "[data-like-button]"
    );

    const buttonText = document.querySelector(
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
        !button
        || !buttonText
        || !countElement
        || !labelElement
        || !errorElement
    ) {
        return;
    }

    let requestInProgress = false;

    button.addEventListener(
        "click",
        async () => {
            if (requestInProgress) {
                return;
            }

            const previousAction =
                button.dataset.action;

            const previousCount =
                getSafeCount(countElement);

            const optimisticCount =
                previousAction === "like"
                    ? previousCount + 1
                    : Math.max(
                        0,
                        previousCount - 1
                    );

            const optimisticAction =
                previousAction === "like"
                    ? "unlike"
                    : "like";

            errorElement.hidden = true;
            requestInProgress = true;
            button.disabled = true;

            applyLikeState({
                button,
                buttonText,
                countElement,
                labelElement,
                action: optimisticAction,
                count: optimisticCount,
            });

            try {
                const data = await sendLikeRequest({
                    url: button.dataset.likeUrl,
                    imageId: button.dataset.imageId,
                    action: previousAction,
                });

                if (!data.changed) {
                    applyLikeState({
                        button,
                        buttonText,
                        countElement,
                        labelElement,
                        action: previousAction,
                        count: previousCount,
                    });
                }

            } catch (error) {
                applyLikeState({
                    button,
                    buttonText,
                    countElement,
                    labelElement,
                    action: previousAction,
                    count: previousCount,
                });

                errorElement.hidden = false;

                console.error(
                    "Could not update image like:",
                    error
                );

            } finally {
                requestInProgress = false;
                button.disabled = false;
            }
        }
    );
}


document.addEventListener(
    "DOMContentLoaded",
    initializeImageLike
);