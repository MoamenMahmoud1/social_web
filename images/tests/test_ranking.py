from unittest.mock import patch

from django.test import SimpleTestCase

from images.ranking import (
    get_image_ranking,
    increment_image_views,
)


class ImageRankingTests(SimpleTestCase):
    @patch("images.ranking.get_redis_client")
    def test_increment_image_views(
        self,
        get_redis_client,
    ):
        redis_client = (
            get_redis_client.return_value
        )

        redis_client.set.return_value = True
        redis_client.zincrby.return_value = 3.0

        result = increment_image_views(
            image_id=10,
            viewer_id=25,
        )

        self.assertEqual(
            result,
            3,
        )

        redis_client.set.assert_called_once_with(
            "images:view:10:user:25",
            "1",
            nx=True,
            ex=3600,
        )

        redis_client.zincrby.assert_called_once_with(
            "images:ranking:views",
            1,
            "10",
        )

    @patch("images.ranking.get_redis_client")
    def test_get_image_ranking(
        self,
        get_redis_client,
    ):
        redis_client = (
            get_redis_client.return_value
        )

        redis_client.zrevrange.return_value = [
            "10",
            "7",
            "3",
        ]

        result = get_image_ranking(
            limit=3
        )

        self.assertEqual(
            result,
            [
                10,
                7,
                3,
            ],
        )

        redis_client.zrevrange.assert_called_once_with(
            "images:ranking:views",
            0,
            2,
        )

    @patch("images.ranking.get_redis_client")
    def test_increment_returns_none_when_redis_fails(
        self,
        get_redis_client,
    ):
        get_redis_client.side_effect = OSError(
            "Redis unavailable"
        )

        result = increment_image_views(
            image_id=10,
            viewer_id=25,
        )

        self.assertIsNone(
            result
        )

    @patch("images.ranking.get_redis_client")
    def test_get_image_ranking_handles_missing_ids(
        self,
        get_redis_client,
    ):
        redis_client = (
            get_redis_client.return_value
        )

        redis_client.zrevrange.return_value = []

        result = get_image_ranking(
            limit=3
        )

        self.assertEqual(
            result,
            [],
        )