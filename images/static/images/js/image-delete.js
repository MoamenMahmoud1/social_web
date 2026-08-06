
"use strict";

(() => {
    const initializeImageDelete = () => {
        if (!window.UI) {
            console.error(
                "The shared UI utilities could not be found."
            );

            return;
        }

        const deleteForm =
            document.querySelector(
                "[data-delete-form]"
            );

        if (!deleteForm) {
            return;
        }

        const deleteButton =
            deleteForm.querySelector(
                ".delete-image-button"
            );

        if (!deleteButton) {
            console.error(
                "The delete button could not be found."
            );

            return;
        }

        let submissionStarted =
            false;

        deleteForm.addEventListener(
            "submit",
            (event) => {
                if (submissionStarted) {
                    event.preventDefault();
                    return;
                }

                const shouldDelete =
                    window.confirm(
                        "Are you sure you want to delete this image? This action cannot be undone."
                    );

                if (!shouldDelete) {
                    event.preventDefault();
                    return;
                }

                submissionStarted =
                    true;

                window.UI.setButtonLoading(
                    deleteButton,
                    {
                        loading: true,
                        loadingText:
                            "Deleting...",
                    }
                );
            }
        );
    };

    if (!window.UI) {
        console.error(
            "ui.js must load before image-delete.js."
        );

        return;
    }

    window.UI.initializeWhenReady(
        initializeImageDelete
    );
})();

