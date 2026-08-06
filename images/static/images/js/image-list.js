"use strict";

(() => {
    const initializeImageFeed = () => {
        const feed = document.querySelector(
            "[data-image-feed]"
        );

        if (!feed) {
            return;
        }

        const imageList = feed.querySelector(
            "[data-image-list]"
        );

        const controls = feed.querySelector(
            "[data-image-feed-controls]"
        );

        if (!imageList || !controls) {
            return;
        }

        const loadMoreLink = controls.querySelector(
            "[data-load-more-images]"
        );

        const loadingMessage = controls.querySelector(
            "[data-images-loading]"
        );

        const errorMessage = controls.querySelector(
            "[data-images-error]"
        );

        const sentinel = controls.querySelector(
            "[data-scroll-sentinel]"
        );

        if (!loadMoreLink) {
            return;
        }

        let isLoading = false;
        let observer = null;

        const setLoadingState = (loading) => {
            isLoading = loading;

            loadMoreLink.classList.toggle(
                "is-loading",
                loading
            );

            loadMoreLink.setAttribute(
                "aria-busy",
                String(loading)
            );

            if (loadingMessage) {
                loadingMessage.hidden = !loading;
            }

            if (
                loading
                && errorMessage
            ) {
                errorMessage.hidden = true;
            }
        };

        const pauseObserver = () => {
            if (
                observer
                && sentinel
            ) {
                observer.unobserve(
                    sentinel
                );
            }
        };

        const resumeObserver = () => {
            if (
                observer
                && sentinel
                && document.body.contains(sentinel)
            ) {
                observer.observe(
                    sentinel
                );
            }
        };

        const stopObserver = () => {
            if (!observer) {
                return;
            }

            observer.disconnect();
            observer = null;
        };

        const removeControls = () => {
            stopObserver();
            controls.remove();
        };

        const appendImages = (html) => {
            const template = document.createElement(
                "template"
            );

            template.innerHTML = html.trim();

            imageList.append(
                template.content
            );
        };

        const createNextUrl = (cursor) => {
            const url = new URL(
                window.location.href
            );

            url.searchParams.set(
                "cursor",
                cursor
            );

            return url.toString();
        };

        const loadNextPage = async () => {
            if (isLoading) {
                return;
            }

            const nextUrl = loadMoreLink.href;

            if (!nextUrl) {
                removeControls();
                return;
            }

            pauseObserver();
            setLoadingState(true);

            try {
                const response = await fetch(
                    nextUrl,
                    {
                        method: "GET",
                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest",
                            "Accept":
                                "application/json",
                        },
                        credentials: "same-origin",
                    }
                );

                if (!response.ok) {
                    throw new Error(
                        `Could not load images: ${response.status}`
                    );
                }

                const data = await response.json();

                if (
                    typeof data.html !== "string"
                ) {
                    throw new Error(
                        "The response does not contain image HTML."
                    );
                }

                appendImages(
                    data.html
                );

                if (
                    data.has_next
                    && data.next_cursor
                ) {
                    loadMoreLink.href =
                        createNextUrl(
                            data.next_cursor
                        );
                } else {
                    removeControls();
                }
            } catch (error) {
                console.error(error);

                if (errorMessage) {
                    errorMessage.hidden = false;
                }
            } finally {
                if (
                    document.body.contains(
                        loadMoreLink
                    )
                ) {
                    setLoadingState(false);
                    resumeObserver();
                }
            }
        };

        loadMoreLink.addEventListener(
            "click",
            (event) => {
                event.preventDefault();

                loadNextPage();
            }
        );

        if (
            sentinel
            && "IntersectionObserver" in window
        ) {
            observer = new IntersectionObserver(
                (entries) => {
                    const entry = entries[0];

                    if (
                        !entry
                        || !entry.isIntersecting
                        || isLoading
                    ) {
                        return;
                    }

                    loadNextPage();
                },
                {
                    root: null,
                    rootMargin: "150px 0px",
                    threshold: 0,
                }
            );

            observer.observe(
                sentinel
            );
        }
    };

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeImageFeed,
            {
                once: true,
            }
        );
    } else {
        initializeImageFeed();
    }
})();

