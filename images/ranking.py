
import logging
from functools import lru_cache

import redis
from django.conf import settings
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)

IMAGE_RANKING_KEY = "images:ranking:views"
IMAGE_VIEW_TTL = 60 * 60


@lru_cache(maxsize=1)
def get_redis_client():
    """
    Create and reuse one Redis client.

    redis-py manages the underlying connection pool.
    Creating the client does not immediately open
    a network connection.
    """

    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
        retry_on_timeout=True,
    )


def build_image_view_key(
    *,
    image_id: int,
    viewer_id: int,
) -> str:
    """
    Build the temporary key used to prevent
    duplicate views from the same user.
    """

    return (
        f"images:view:{image_id}:"
        f"user:{viewer_id}"
    )


def increment_image_views(
    *,
    image_id: int,
    viewer_id: int,
) -> int | None:
    """
    Increment an image's Redis ranking score once per viewer window.

    Uses a temporary per-viewer key to avoid counting repeated page loads
    during the configured TTL. Redis failures are treated as non-fatal so
    image pages remain available when ranking infrastructure is unavailable.

    Returns:
        float | None: Updated score, or None if Redis is unavailable.
    """

    if image_id <= 0 or viewer_id <= 0:
        return None

    view_key = build_image_view_key(
        image_id=image_id,
        viewer_id=viewer_id,
    )

    try:
        redis_client = get_redis_client()

        is_new_view = redis_client.set(
            view_key,
            "1",
            nx=True,
            ex=IMAGE_VIEW_TTL,
        )

        if is_new_view:
            score = redis_client.zincrby(
                IMAGE_RANKING_KEY,
                1,
                str(image_id),
            )
        else:
            score = redis_client.zscore(
                IMAGE_RANKING_KEY,
                str(image_id),
            )

        return int(
            float(score or 0)
        )

    except (
        RedisError,
        OSError,
        TypeError,
        ValueError,
    ):
        logger.exception(
            "Could not register a view for image %s",
            image_id,
        )

        return None


def get_image_ranking(
    limit: int = 10,
) -> list[int]:
    """
    Return image IDs ordered from most viewed
    to least viewed.

    If Redis is unavailable, return an empty list
    so the ranking page remains available.
    """

    if limit <= 0:
        return []

    try:
        redis_client = get_redis_client()

        image_ids = redis_client.zrevrange(
            IMAGE_RANKING_KEY,
            0,
            limit - 1,
        )

        return [
            int(image_id)
            for image_id in image_ids
        ]

    except (
        RedisError,
        OSError,
        ValueError,
    ):
        logger.exception(
            "Could not read image ranking"
        )

        return []


def redis_is_available() -> bool:
    """
    Return True when Redis responds to PING.
    """

    try:
        return bool(
            get_redis_client().ping()
        )

    except (
        RedisError,
        OSError,
    ):
        return False

def remove_image_from_ranking(
    image_id: int,
) -> bool:
    """
    Remove a deleted image from the Redis ranking.

    Temporary view-deduplication keys are left to expire
    automatically according to their TTL.
    """

    if image_id <= 0:
        return False

    try:
        redis_client = get_redis_client()

        redis_client.zrem(
            IMAGE_RANKING_KEY,
            str(image_id),
        )

        return True

    except (
        RedisError,
        OSError,
    ):
        logger.exception(
            "Could not remove image %s from ranking",
            image_id,
        )

        return False