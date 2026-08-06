from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from action.models import Action


class Image(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="images_created",
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        max_length=200,
    )

    slug = models.SlugField(
        max_length=200,
        blank=True,
    )

    url = models.URLField(
        max_length=200,
    )

    image = models.ImageField(
        upload_to="images/%y/%m/%d/",
    )

    description = models.TextField(
        blank=True,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    users_like = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="images_liked",
        blank=True,
    )

    total_likes = models.PositiveIntegerField(
        default=0,
        editable=False,
    )

    actions = GenericRelation(
        Action,
        content_type_field="target_ct",
        object_id_field="target_id",
        related_query_name="image_target",
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
                name="image_created_idx",
            ),
            models.Index(
                fields=[
                    "-total_likes",
                ],
                name="image_likes_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    total_likes__gte=0,
                ),
                name="image_total_likes_gte_0",
            ),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "images:detail",
            args=[
                self.id,
                self.slug,
            ],
        )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(
                self.title
            )

        super().save(
            *args,
            **kwargs,
        )

