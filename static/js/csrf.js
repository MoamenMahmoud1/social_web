"use strict";

(() => {
    const getCookie = (name) => {
        const cookieValue = document.cookie
            .split(";")
            .map((cookie) => cookie.trim())
            .find((cookie) => {
                return cookie.startsWith(
                    `${name}=`
                );
            });

        if (!cookieValue) {
            return null;
        }

        return decodeURIComponent(
            cookieValue.slice(
                name.length + 1
            )
        );
    };

    window.getCSRFToken = () => {
        return getCookie(
            "csrftoken"
        );
    };
})();