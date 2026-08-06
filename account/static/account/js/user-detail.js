
"use strict";

(() => {
    const initializeFollowButton = () => {
        const followButton = document.querySelector(
            "[data-follow-button]"
        );

        if (!followButton) {
            return;
        }

        const followerTotal = document.querySelector(
            "[data-follower-total]"
        );

        const followerLabel = document.querySelector(
            "[data-follower-label]"
        );

        const updateFollowerText = (total) => {
            if (followerTotal) {
                followerTotal.textContent = String(total);
            }

            if (followerLabel) {
                followerLabel.textContent =
                    total === 1
                        ? "follower"
                        : "followers";
            }
        };

        const setLoadingState = (isLoading) => {
            followButton.disabled = isLoading;
            followButton.classList.toggle(
                "is-loading",
                isLoading
            );

            followButton.setAttribute(
                "aria-busy",
                String(isLoading)
            );
        };

        followButton.addEventListener(
            "click",
            async () => {
                if (followButton.disabled) {
                    return;
                }

                const previousAction =
                    followButton.dataset.action;

                const requestUrl =
                    followButton.dataset.followUrl;

                const userId =
                    followButton.dataset.userId;

                if (
                    !requestUrl
                    || !userId
                    || !previousAction
                ) {
                    console.error(
                        "Follow button data is incomplete."
                    );

                    return;
                }

                const csrfToken =
                    typeof window.getCSRFToken === "function"
                        ? window.getCSRFToken()
                        : null;

                if (!csrfToken) {
                    console.error(
                        "CSRF token could not be found."
                    );

                    return;
                }

                const formData = new FormData();

                formData.append("id", userId);
                formData.append(
                    "action",
                    previousAction
                );

                setLoadingState(true);

                try {
                    const response = await fetch(
                        requestUrl,
                        {
                            method: "POST",
                            headers: {
                                "X-CSRFToken": csrfToken,
                            },
                            mode: "same-origin",
                            body: formData,
                        }
                    );

                    if (!response.ok) {
                        throw new Error(
                            "Could not update follow status."
                        );
                    }

                    const data = await response.json();

                    if (data.status !== "ok") {
                        throw new Error(
                            "The server rejected the request."
                        );
                    }

                    const nextAction =
                        previousAction === "follow"
                            ? "unfollow"
                            : "follow";

                    const isFollowing =
                        nextAction === "unfollow";

                    followButton.dataset.action =
                        nextAction;

                    followButton.textContent =
                        isFollowing
                            ? "Unfollow"
                            : "Follow";

                    followButton.setAttribute(
                        "aria-pressed",
                        String(isFollowing)
                    );

                    followButton.classList.toggle(
                        "is-following",
                        isFollowing
                    );

                    const currentTotal =
                        Number.parseInt(
                            followerTotal?.textContent || "0",
                            10
                        ) || 0;

                    const nextTotal =
                        previousAction === "follow"
                            ? currentTotal + 1
                            : Math.max(
                                currentTotal - 1,
                                0
                            );

                    updateFollowerText(nextTotal);
                } catch (error) {
                    console.error(error);
                } finally {
                    setLoadingState(false);
                }
            }
        );

        followButton.classList.toggle(
            "is-following",
            followButton.dataset.action === "unfollow"
        );
    };

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeFollowButton,
            {
                once: true,
            }
        );
    } else {
        initializeFollowButton();
    }
})();

