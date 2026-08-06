"use strict";

(() => {
    const initializeImageFeed = () => {
        if (!window.UI) {
            console.error(
                "ui.js must load before image-list.js."
            );

            return;
        }

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

            loadMoreLink.setAttribute(
                "aria-disabled",
                String(loading)
            );

            if (loadingMessage) {
                loadingMessage.hidden = !loading;
            }

            if (loading) {
                window.UI.hideError(
                    errorMessage
                );
            }
        };

        const pauseObserver = () => {
            if (!observer || !sentinel) {
                return;
            }

            observer.unobserve(
                sentinel
            );
        };

        const resumeObserver = () => {
            if (
                !observer
                || !sentinel
                || !document.body.contains(
                    sentinel
                )
            ) {
                return;
            }

            observer.observe(
                sentinel
            );
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
            const template =
                document.createElement(
                    "template"
                );

            template.innerHTML =
                html.trim();

            imageList.append(
                template.content
            );
        };

        const createNextUrl = (
            cursor
        ) => {
            const url = new URL(
                window.location.href
            );

            url.searchParams.set(
                "cursor",
                cursor
            );

            return url.toString();
        };

        const parseResponse = async (
            response
        ) => {
            let data;

            try {
                data =
                    await response.json();
            } catch {
                throw new Error(
                    "The server returned an invalid response."
                );
            }

            if (!response.ok) {
                throw new Error(
                    data.message
                    || `Could not load images: ${response.status}`
                );
            }

            if (
                typeof data.html
                !== "string"
            ) {
                throw new Error(
                    "The response does not contain image HTML."
                );
            }

            return data;
        };

        const loadNextPage = async () => {
            if (isLoading) {
                return;
            }

            const nextUrl =
                loadMoreLink.href;

            if (!nextUrl) {
                removeControls();
                return;
            }

            pauseObserver();
            setLoadingState(true);

            try {
                const response =
                    await fetch(
                        nextUrl,
                        {
                            method: "GET",
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
                    await parseResponse(
                        response
                    );

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

                    return;
                }

                removeControls();
            } catch (error) {
                window.UI.showError(
                    errorMessage,
                    error.message
                    || "We could not load more images."
                );

                console.error(
                    "Could not load more images:",
                    error
                );
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

                if (isLoading) {
                    return;
                }

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
                        const entry =
                            entries[0];

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
                        rootMargin:
                            "150px 0px",
                        threshold: 0,
                    }
                );

            observer.observe(
                sentinel
            );
        }
    };

    if (!window.UI) {
        console.error(
            "ui.js must load before image-list.js."
        );

        return;
    }

    window.UI.initializeWhenReady(
        initializeImageFeed
    );
})();

