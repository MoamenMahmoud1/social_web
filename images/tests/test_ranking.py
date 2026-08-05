from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from redis.exceptions import RedisError

from images.ranking import (
    get_image_ranking,
    increment_image_views,
)


class ImageRankingTests(SimpleTestCase):
    @patch("images.ranking.get_redis_client")
    def test_increment_image_views(self, mock_get_redis_client):
        redis_client = Mock()
        redis_client.zincrby.return_value = 6.0
        mock_get_redis_client.return_value = redis_client

        result = increment_image_views(image_id=10)

        redis_client.zincrby.assert_called_once_with(
            "image_ranking",
            1,
            "10",
        )
        self.assertEqual(result, 6.0)

    @patch("images.ranking.get_redis_client")
    def test_get_image_ranking(self, mock_get_redis_client):
        redis_client = Mock()
        redis_client.zrevrange.return_value = ["8", "3", "12"]
        mock_get_redis_client.return_value = redis_client

        result = get_image_ranking(limit=3)

        redis_client.zrevrange.assert_called_once_with(
            "image_ranking",
            0,
            2,
        )
        self.assertEqual(result, [8, 3, 12])

    @patch("images.ranking.get_redis_client")
    def test_increment_returns_none_when_redis_fails(
        self,
        mock_get_redis_client,
    ):
        mock_get_redis_client.side_effect = RedisError(
            "Redis is unavailable"
        )

        result = increment_image_views(image_id=10)

        self.assertIsNone(result)

    @patch("images.ranking.get_redis_client")
    def test_ranking_returns_empty_list_when_redis_fails(
        self,
        mock_get_redis_client,
    ):
        mock_get_redis_client.side_effect = RedisError(
            "Redis is unavailable"
        )

        result = get_image_ranking()

        self.assertEqual(result, [])