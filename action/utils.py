import datetime

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Action


def create_action(user, verb, target=None):
    last_minute = timezone.now() - datetime.timedelta(seconds=60)

    similar_actions = Action.objects.filter(
        user_id=user.id,
        verb=verb,
        created__gte=last_minute,
    )

    if target is not None:
        target_ct = ContentType.objects.get_for_model(target)

        similar_actions = similar_actions.filter(
            target_ct=target_ct,
            target_id=target.pk,
        )

    if similar_actions.exists():
        return False

    Action.objects.create(
        user=user,
        verb=verb,
        target=target,
    )

    return True