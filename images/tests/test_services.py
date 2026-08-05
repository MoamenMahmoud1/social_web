import socket
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from images.services import (
    MAX_DOWNLOAD_SIZE,
    read_limited_content,
    validate_public_url,
)
import io

from PIL import Image as PillowImage
from images.services import sanitize_image


class ValidatePublicUrlTests(SimpleTestCase):
    @patch("images.services.socket.getaddrinfo")
    def test_rejects_private_ip(self, mock_getaddrinfo):
        mock_getaddrinfo.return_value = [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                ("127.0.0.1", 80),
            )
        ]

        with self.assertRaises(ValidationError):
            validate_public_url("http://example.com/image.jpg")

    def test_rejects_unsupported_scheme(self):
        with self.assertRaises(ValidationError):
            validate_public_url("file:///etc/passwd")

    def test_rejects_unsafe_port(self):
        with self.assertRaises(ValidationError):
            validate_public_url(
                "http://example.com:6379/image.jpg"
            )


class ReadLimitedContentTests(SimpleTestCase):
    def test_rejects_large_content_length(self):
        response = Mock()
        response.headers = {
            "Content-Length": str(MAX_DOWNLOAD_SIZE + 1)
        }

        with self.assertRaises(ValidationError):
            read_limited_content(response)

    def test_rejects_large_streamed_file(self):
        response = Mock()
        response.headers = {}
        response.iter_content.return_value = [
            b"a" * MAX_DOWNLOAD_SIZE,
            b"b",
        ]

        with self.assertRaises(ValidationError):
            read_limited_content(response)

    def test_returns_valid_content(self):
        response = Mock()
        response.headers = {}
        response.iter_content.return_value = [
            b"hello",
            b"world",
        ]

        content = read_limited_content(response)

        self.assertEqual(content, b"helloworld")



class SanitizeImageTests(SimpleTestCase):
    def create_image_bytes(self, image_format="PNG"):
        output = io.BytesIO()

        image = PillowImage.new(
            mode="RGB",
            size=(100, 100),
            color="white",
        )
        image.save(output, format=image_format)

        return output.getvalue()

    def test_rejects_fake_image(self):
        with self.assertRaises(ValidationError):
            sanitize_image(b"<html>not an image</html>")

    def test_sanitizes_valid_image(self):
        content = self.create_image_bytes()

        clean_file, extension = sanitize_image(content)

        self.assertEqual(extension, ".png")
        self.assertGreater(clean_file.size, 0)

        with PillowImage.open(clean_file) as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (100, 100))