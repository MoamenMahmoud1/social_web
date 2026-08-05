from datetime import timedelta

from django.contrib.contenttypes.models import (
    ContentType,
)
from django.utils import timezone

from .models import Action


ACTION_DUPLICATE_WINDOW_SECONDS = 60


def create_action(user, verb, target=None):
    last_minute = timezone.now() - timedelta(
        seconds=ACTION_DUPLICATE_WINDOW_SECONDS,
    )

    action_data = {
        "user_id": user.id,
        "verb": verb,
    }

    similar_actions = Action.objects.filter(
        user_id=user.id,
        verb=verb,
        created__gte=last_minute,
    )

    if target is not None:
        target_ct = ContentType.objects.get_for_model(
            target,
            for_concrete_model=False,
        )

        action_data.update(
            {
                "target_ct_id": target_ct.id,
                "target_id": target.pk,
            }
        )

        similar_actions = similar_actions.filter(
            target_ct_id=target_ct.id,
            target_id=target.pk,
        )

    else:
        similar_actions = similar_actions.filter(
            target_ct__isnull=True,
            target_id__isnull=True,
        )

    if similar_actions.exists():
        return False

    Action.objects.create(
        **action_data,
    )

    return True