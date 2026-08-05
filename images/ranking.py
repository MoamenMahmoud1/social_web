import logging

import redis
from django.conf import settings
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)

RANKING_KEY = "image_ranking"


def get_redis_client():
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


def increment_image_views(image_id):
    try:
        redis_client = get_redis_client()

        return redis_client.zincrby(
            RANKING_KEY,
            1,
            str(image_id),
        )

    except RedisError:
        logger.exception(
            "Could not increment views for image %s",
            image_id,
        )
        return None


def get_image_ranking(limit=10):
    try:
        redis_client = get_redis_client()

        image_ids = redis_client.zrevrange(
            RANKING_KEY,
            0,
            limit - 1,
        )

        return [int(image_id) for image_id in image_ids]

    except (RedisError, ValueError):
        logger.exception("Could not read image ranking")
        return []