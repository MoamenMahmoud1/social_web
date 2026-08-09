import io
import ipaddress
import socket
import warnings
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image as PillowImage
from PIL import ImageOps, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile


MAX_DOWNLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_PIXELS = 25_000_000
MAX_REDIRECTS = 3
CHUNK_SIZE = 8 * 1024  # 8 KB

ALLOWED_PORTS = {80, 443}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

SAFE_IMAGE_FORMATS = {
    "JPEG": ("JPEG", ".jpg"),
    "PNG": ("PNG", ".png"),
    "WEBP": ("WEBP", ".webp"),
}


def validate_public_url(url):
    """
    Validate an externally supplied image URL before connecting to it.

    Rejects unsupported schemes, embedded credentials, non-standard ports,
    unresolved hosts, and IP addresses that are not globally routable.

    Raises:
        ValidationError: If the URL is unsafe or cannot be resolved.
    """

    parsed_url = urlparse(url)

    if parsed_url.scheme not in {"http", "https"}:
        raise ValidationError(
            "Only HTTP and HTTPS URLs are allowed."
        )

    if not parsed_url.hostname:
        raise ValidationError("Invalid image URL.")

    if parsed_url.username or parsed_url.password:
        raise ValidationError(
            "URLs containing credentials are not allowed."
        )

    try:
        port = parsed_url.port
    except ValueError as exc:
        raise ValidationError("Invalid network port.") from exc

    if port is not None and port not in ALLOWED_PORTS:
        raise ValidationError(
            "Only ports 80 and 443 are allowed."
        )

    try:
        addresses = socket.getaddrinfo(
            parsed_url.hostname,
            port or (443 if parsed_url.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValidationError(
            "Could not resolve the URL hostname."
        ) from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if not ip.is_global:
            raise ValidationError(
                "Private or internal addresses are not allowed."
            )


def get_safe_response(url):
    """
    Send the request while validating every redirect manually.
    """

    current_url = url

    for _ in range(MAX_REDIRECTS + 1):
        validate_public_url(current_url)

        try:
            response = requests.get(
                current_url,
                stream=True,
                allow_redirects=False,
                timeout=(5, 10),
                headers={
                    "User-Agent": "SocialWeb-ImageFetcher/1.0",
                    "Accept": "image/jpeg,image/png,image/webp",
                },
            )
        except requests.RequestException as exc:
            raise ValidationError(
                "Could not download the image."
            ) from exc

        if response.is_redirect:
            redirect_url = response.headers.get("Location")
            response.close()

            if not redirect_url:
                raise ValidationError(
                    "The server returned an invalid redirect."
                )

            current_url = urljoin(current_url, redirect_url)
            continue

        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            response.close()
            raise ValidationError(
                "The image server returned an error."
            ) from exc

        return response

    raise ValidationError(
        "The URL contains too many redirects."
    )


def read_limited_content(response):
    """
    Download the file gradually without allowing more than 5 MB.
    """

    content_length = response.headers.get("Content-Length")

    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = None

        if declared_size and declared_size > MAX_DOWNLOAD_SIZE:
            raise ValidationError(
                "The image must not exceed 5 MB."
            )

    content = bytearray()

    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if not chunk:
            continue

        content.extend(chunk)

        if len(content) > MAX_DOWNLOAD_SIZE:
            raise ValidationError(
                "The image must not exceed 5 MB."
            )

    if not content:
        raise ValidationError("The downloaded image is empty.")

    return bytes(content)


def sanitize_image(content):
    """
    Decode the real image and create a new clean image from its pixels.
    """

    PillowImage.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS

    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                PillowImage.DecompressionBombWarning,
            )

            with PillowImage.open(io.BytesIO(content)) as image:
                image.verify()

        with PillowImage.open(io.BytesIO(content)) as image:
            image.load()

            if getattr(image, "is_animated", False):
                raise ValidationError(
                    "Animated images are not supported."
                )

            format_data = SAFE_IMAGE_FORMATS.get(image.format)

            if format_data is None:
                raise ValidationError(
                    "Unsupported image format."
                )

            output_format, extension = format_data

            # Applies the EXIF rotation before deleting the metadata.
            clean_image = ImageOps.exif_transpose(image)

            if output_format == "JPEG":
                clean_image = clean_image.convert("RGB")
            else:
                clean_image = clean_image.copy()

            output = io.BytesIO()

            save_options = {
                "format": output_format,
                "optimize": True,
            }

            if output_format == "JPEG":
                save_options["quality"] = 85

            clean_image.save(output, **save_options)

    except ValidationError:
        raise
    except (
        UnidentifiedImageError,
        PillowImage.DecompressionBombWarning,
        PillowImage.DecompressionBombError,
        OSError,
        ValueError,
    ) as exc:
        raise ValidationError(
            "The downloaded file is not a safe image."
        ) from exc

    output.seek(0)

    return ContentFile(output.read()), extension


def download_safe_image(url):
    """
    Complete process:
    validate URL → download → validate type → sanitize image.
    """

    response = get_safe_response(url)

    try:
        content_type = response.headers.get(
            "Content-Type",
            "",
        ).split(";", maxsplit=1)[0].strip().lower()

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                "The URL does not point to a supported image."
            )

        content = read_limited_content(response)

    finally:
        response.close()

    return sanitize_image(content)