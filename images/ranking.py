import logging
from functools import lru_cache

import redis
from django.conf import settings
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)

IMAGE_RANKING_KEY = "images:ranking:views"


@lru_cache(maxsize=1)
def get_redis_client():
    """
    Create and reuse one Redis connection-pool client.

    redis-py manages the underlying connection pool.
    Creating this client does not immediately connect;
    the connection is opened when a Redis command runs.
    """

    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
        retry_on_timeout=True,
    )


def increment_image_views(image_id):
    """
    Increment the view score for one image.

    Return the updated score as an integer.

    Redis ranking is a non-critical feature. If Redis is
    unavailable, return None and allow the page to load.
    """

    try:
        redis_client = get_redis_client()

        updated_score = redis_client.zincrby(
            IMAGE_RANKING_KEY,
            1,
            str(image_id),
        )

        return int(updated_score)

    except (RedisError, OSError):
        logger.exception(
            "Could not increment views for image %s",
            image_id,
        )

        return None


def get_image_ranking(limit=10):
    """
    Return image IDs ordered from most viewed to least viewed.

    If Redis is unavailable, return an empty list so the
    ranking page remains available.
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

    except (RedisError, OSError, ValueError):
        logger.exception(
            "Could not read image ranking",
        )

        return []


def redis_is_available():
    """
    Return True when Redis responds to PING.
    Useful for checks and tests.
    """

    try:
        return bool(
            get_redis_client().ping()
        )

    except (RedisError, OSError):
        return False