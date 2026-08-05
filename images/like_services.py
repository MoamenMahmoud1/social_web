from dataclasses import dataclass

from django.db import transaction
from django.db.models import F

from action.utils import create_action

from .models import Image


@dataclass(frozen=True)
class LikeResult:
    changed: bool
    action: str


def change_image_like(
    *,
    image: Image,
    user,
    action: str,
) -> LikeResult:
    """
    Add or remove an image like while keeping total_likes synchronized.

    The ManyToMany table is the source of truth.
    Image.total_likes is a denormalized counter used for fast reads.
    """

    if action not in {"like", "unlike"}:
        raise ValueError("Unsupported like action.")

    through_model = Image.users_like.through

    with transaction.atomic():
        if action == "like":
            _, created = through_model.objects.get_or_create(
                image_id=image.id,
                user_id=user.id,
            )

            if not created:
                return LikeResult(
                    changed=False,
                    action=action,
                )

            Image.objects.filter(
                id=image.id,
            ).update(
                total_likes=F("total_likes") + 1,
            )

            create_action(
                user,
                "likes",
                image,
            )

            return LikeResult(
                changed=True,
                action=action,
            )

        deleted_count, _ = through_model.objects.filter(
            image_id=image.id,
            user_id=user.id,
        ).delete()

        if deleted_count == 0:
            return LikeResult(
                changed=False,
                action=action,
            )

        Image.objects.filter(
            id=image.id,
            total_likes__gt=0,
        ).update(
            total_likes=F("total_likes") - 1,
        )

        return LikeResult(
            changed=True,
            action=action,
        )