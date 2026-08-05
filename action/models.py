from django.conf import settings
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
)
from django.contrib.contenttypes.models import (
    ContentType,
)
from django.db import models


class Action(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="actions",
        on_delete=models.CASCADE,
    )

    verb = models.CharField(
        max_length=255,
    )

    target_ct = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        related_name="target_actions",
        on_delete=models.CASCADE,
    )

    target_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    target = GenericForeignKey(
        "target_ct",
        "target_id",
    )

    created = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created",
        ]

        indexes = [
            models.Index(
                fields=[
                    "-created",
                ],
                name="action_created_idx",
            ),
            models.Index(
                fields=[
                    "user",
                    "verb",
                    "-created",
                ],
                name="action_user_verb_idx",
            ),
            models.Index(
                fields=[
                    "target_ct",
                    "target_id",
                ],
                name="action_target_idx",
            ),
        ]

    def __str__(self):
        return f"{self.user} {self.verb}"