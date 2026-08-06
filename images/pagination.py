
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, TypeVar

from django.core import signing
from django.db.models import Q, QuerySet
from django.utils.dateparse import parse_datetime


T = TypeVar("T")

IMAGE_BATCH_SIZE = 10
IMAGE_CURSOR_SALT = "images.image-feed.cursor"
IMAGE_CURSOR_MAX_AGE = 60 * 60 * 24


@dataclass(frozen=True)
class CursorBatch(Generic[T]):
    """
    Represents one cursor-paginated result batch.
    """

    items: list[T]
    has_next: bool
    next_cursor: str | None


class InvalidCursorError(ValueError):
    """
    Raised when the cursor is invalid, modified,
    expired, or contains malformed data.
    """


def encode_image_cursor(*, created: datetime, image_id: int) -> str:
    """
    Create a signed cursor from the final displayed image.
    """

    return signing.dumps(
        {
            "created": created.isoformat(),
            "id": image_id,
        },
        salt=IMAGE_CURSOR_SALT,
        compress=True,
    )


def decode_image_cursor(cursor: str) -> tuple[datetime, int]:
    """
    Validate and decode a signed image cursor.
    """

    try:
        cursor_data = signing.loads(
            cursor,
            salt=IMAGE_CURSOR_SALT,
            max_age=IMAGE_CURSOR_MAX_AGE,
        )

        created_value = cursor_data["created"]
        image_id = int(cursor_data["id"])

        created = parse_datetime(created_value)

        if created is None:
            raise ValueError(
                "Cursor contains an invalid datetime."
            )

        if image_id <= 0:
            raise ValueError(
                "Cursor contains an invalid image ID."
            )

    except (
        signing.BadSignature,
        signing.SignatureExpired,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise InvalidCursorError(
            "The image cursor is invalid or expired."
        ) from error

    return created, image_id


def paginate_images_by_cursor(
    queryset: QuerySet[T],
    *,
    cursor: str | None = None,
    batch_size: int = IMAGE_BATCH_SIZE,
) -> CursorBatch[T]:
    """
    Return one image batch using keyset pagination.

    The queryset must contain `created` and `id` fields
    and must represent images ordered newest-first.
    """

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be greater than zero."
        )

    queryset = queryset.order_by(
        "-created",
        "-id",
    )

    if cursor:
        cursor_created, cursor_id = decode_image_cursor(
            cursor
        )

        queryset = queryset.filter(
            Q(created__lt=cursor_created)
            | Q(
                created=cursor_created,
                id__lt=cursor_id,
            )
        )

    fetched_items = list(
        queryset[: batch_size + 1]
    )

    has_next = len(fetched_items) > batch_size
    items = fetched_items[:batch_size]

    next_cursor = None

    if has_next and items:
        final_item = items[-1]

        next_cursor = encode_image_cursor(
            created=final_item.created,
            image_id=final_item.pk,
        )

    return CursorBatch(
        items=items,
        has_next=has_next,
        next_cursor=next_cursor,
    )

