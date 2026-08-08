"use strict";

(() => {
    const initializeFollowButton = () => {
        const button = document.querySelector(
            "[data-follow-button]"
        );

        if (!button) {
            return;
        }

        const totalElement = document.querySelector(
            "[data-follower-total]"
        );

        const labelElement = document.querySelector(
            "[data-follower-label]"
        );

        const updateButton = (action) => {
            const following =
                action === "unfollow";

            button.dataset.action = action;

            button.textContent =
                following
                    ? "Unfollow"
                    : "Follow";

            button.classList.toggle(
                "is-following",
                following
            );

            button.setAttribute(
                "aria-pressed",
                String(following)
            );
        };

        const updateTotal = (total) => {
            if (totalElement) {
                totalElement.textContent =
                    String(total);
            }

            if (labelElement) {
                labelElement.textContent =
                    total === 1
                        ? "follower"
                        : "followers";
            }
        };

        button.addEventListener(
            "click",
            async () => {
                const action =
                    button.dataset.action;

                if (
                    button.disabled
                    || !["follow", "unfollow"]
                        .includes(action)
                ) {
                    return;
                }

                const csrfToken =
                    window.getCSRFToken?.();

                if (!csrfToken) {
                    return;
                }

                const formData =
                    new FormData();

                formData.append(
                    "id",
                    button.dataset.userId
                );

                formData.append(
                    "action",
                    action
                );

                window.UI.setButtonLoading(
                    button
                );

                try {
                    const response =
                        await fetch(
                            button.dataset.followUrl,
                            {
                                method: "POST",
                                headers: {
                                    "X-CSRFToken":
                                        csrfToken,
                                    "X-Requested-With":
                                        "XMLHttpRequest",
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
                        return;
                    }

                    updateButton(
                        action === "follow"
                            ? "unfollow"
                            : "follow"
                    );

                    updateTotal(
                        data.total_followers
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
        initializeFollowButton
    );
})();