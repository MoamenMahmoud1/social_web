"use strict";

const siteUrl = "http://127.0.0.1:8000/";
const bookmarkletCssUrl =
    `${siteUrl}static/images/css/bookmarklet.css`;

const minWidth = 1;
const minHeight = 1;


function loadBookmarkletCss() {
    const existingLink = document.querySelector(
        'link[data-bookmarklet-css]'
    );

    if (existingLink) {
        return;
    }

    const link = document.createElement("link");

    link.rel = "stylesheet";
    link.href = `${bookmarkletCssUrl}?r=${Date.now()}`;
    link.dataset.bookmarkletCss = "true";

    document.head.appendChild(link);
}


function createBookmarkletBox() {
    let bookmarklet = document.getElementById(
        "bookmarklet"
    );

    if (bookmarklet) {
        return bookmarklet;
    }

    bookmarklet = document.createElement("div");

    bookmarklet.id = "bookmarklet";
    bookmarklet.hidden = true;

    bookmarklet.innerHTML = `
        <button
            type="button"
            id="bookmarklet-close"
            aria-label="Close"
        >
            &times;
        </button>

        <h1>Select an image to bookmark:</h1>

        <div class="images"></div>
    `;

    document.body.appendChild(bookmarklet);

    return bookmarklet;
}


function getImageUrl(image) {
    return (
        image.currentSrc
        || image.getAttribute("src")
        || image.src
        || ""
    );
}


function getValidImages() {
    return Array.from(
        document.querySelectorAll("img")
    ).filter((image) => {
        const imageUrl = getImageUrl(image);

        return (
            imageUrl
            && image.complete
            && image.naturalWidth >= minWidth
            && image.naturalHeight >= minHeight
            && !image.closest("#bookmarklet")
        );
    });
}


function openImageCreatePage(imageUrl) {
    const createUrl = new URL(
        "images/create/",
        siteUrl
    );

    createUrl.searchParams.set(
        "url",
        imageUrl
    );

    createUrl.searchParams.set(
        "title",
        document.title
    );

    window.open(
        createUrl.toString(),
        "_blank",
        "noopener,noreferrer"
    );
}


function createSelectableImage(sourceImage) {
    const selectableImage =
        document.createElement("img");

    selectableImage.src =
        getImageUrl(sourceImage);

    selectableImage.alt =
        sourceImage.alt || "Selectable image";

    selectableImage.loading = "lazy";
    selectableImage.tabIndex = 0;

    const selectImage = () => {
        const bookmarklet = document.getElementById(
            "bookmarklet"
        );

        if (bookmarklet) {
            bookmarklet.hidden = true;
        }

        openImageCreatePage(
            selectableImage.src
        );
    };

    selectableImage.addEventListener(
        "click",
        selectImage
    );

    selectableImage.addEventListener(
        "keydown",
        (event) => {
            if (
                event.key === "Enter"
                || event.key === " "
            ) {
                event.preventDefault();
                selectImage();
            }
        }
    );

    return selectableImage;
}


function bookmarkletLaunch() {
    const bookmarklet = createBookmarkletBox();

    const closeButton = bookmarklet.querySelector(
        "#bookmarklet-close"
    );

    const imagesContainer = bookmarklet.querySelector(
        ".images"
    );

    imagesContainer.replaceChildren();

    const pageImages = getValidImages();

    if (pageImages.length === 0) {
        const message = document.createElement("p");

        message.textContent =
            "No images were found on this page.";

        imagesContainer.appendChild(message);

    } else {
        pageImages.forEach((image) => {
            const selectableImage =
                createSelectableImage(image);

            imagesContainer.appendChild(
                selectableImage
            );
        });
    }

    closeButton.onclick = () => {
        bookmarklet.hidden = true;
    };

    bookmarklet.hidden = false;
}


loadBookmarkletCss();
createBookmarkletBox();
bookmarkletLaunch();