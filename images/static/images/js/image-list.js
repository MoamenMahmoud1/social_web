"use strict";

(() => {
    const initializeImageFeed = () => {
        const feed = document.querySelector(
            "[data-image-feed]"
        );

        if (!feed || !window.UI) {
            return;
        }

        const list = feed.querySelector(
            "[data-image-list]"
        );

        const controls = feed.querySelector(
            "[data-image-feed-controls]"
        );

        if (!list || !controls) {
            return;
        }

        const loadMore = controls.querySelector(
            "[data-load-more-images]"
        );

        const loading = controls.querySelector(
            "[data-images-loading]"
        );

        const error = controls.querySelector(
            "[data-images-error]"
        );

        const sentinel = controls.querySelector(
            "[data-scroll-sentinel]"
        );

        if (!loadMore) {
            return;
        }

        let isLoading = false;
        let observer;

        const setLoading = (state) => {
            isLoading = state;

            loadMore.classList.toggle(
                "is-loading",
                state
            );

            loadMore.setAttribute(
                "aria-busy",
                String(state)
            );

            loadMore.setAttribute(
                "aria-disabled",
                String(state)
            );

            if (loading) {
                loading.hidden = !state;
            }

            if (state) {
                window.UI.hideError(error);
            }
        };

        const appendImages = (html) => {
            const template =
                document.createElement(
                    "template"
                );

            template.innerHTML =
                html.trim();

            list.append(
                template.content
            );
        };

        const setNextCursor = (cursor) => {
            const url = new URL(
                loadMore.href
            );

            url.searchParams.set(
                "cursor",
                cursor
            );

            loadMore.href =
                url.toString();
        };

        const finishFeed = () => {
            observer?.disconnect();
            controls.remove();
        };

        const loadNextPage = async () => {
            if (isLoading) {
                return;
            }

            setLoading(true);

            try {
                const response = await fetch(
                    loadMore.href,
                    {
                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest",
                            "Accept":
                                "application/json",
                        },
                        credentials:
                            "same-origin",
                    }
                );

                const data =
                    await response.json();

                if (
                    !response.ok
                    || typeof data.html
                        !== "string"
                ) {
                    throw new Error(
                        data.message
                        || "We could not load more images."
                    );
                }

                appendImages(
                    data.html
                );

                if (
                    data.has_next
                    && data.next_cursor
                ) {
                    setNextCursor(
                        data.next_cursor
                    );

                    return;
                }

                finishFeed();
            } catch (requestError) {
                window.UI.showError(
                    error,
                    requestError.message
                    || "We could not load more images."
                );
            } finally {
                if (
                    document.body.contains(
                        controls
                    )
                ) {
                    setLoading(false);
                }
            }
        };

        loadMore.addEventListener(
            "click",
            (event) => {
                event.preventDefault();

                loadNextPage();
            }
        );

        if (
            sentinel
            && "IntersectionObserver"
                in window
        ) {
            observer =
                new IntersectionObserver(
                    (entries) => {
                        if (
                            entries[0]
                                .isIntersecting
                        ) {
                            loadNextPage();
                        }
                    },
                    {
                        rootMargin:
                            "300px 0px",
                    }
                );

            observer.observe(
                sentinel
            );
        }
    };

    window.UI.initializeWhenReady(
        initializeImageFeed
    );
})();
