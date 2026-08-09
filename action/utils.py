
from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from .models import Action


ACTION_DUPLICATE_WINDOW_SECONDS = 60


def create_action(user, verb, target=None):
    """
    Create a user activity entry while suppressing near-duplicate actions.

    Similar actions from the same user are ignored when they occur within
    a short time window. This keeps the activity stream from being flooded
    by repeated operations such as rapid likes, follows, or bookmarks.

    Args:
        user: User responsible for the activity.
        verb: Human-readable description of the action.
        target: Optional object associated with the activity.

    Returns:
        bool: True when a new action is created, otherwise False.
    """

    if user is None or user.pk is None:
        raise ValueError(
            "create_action() requires a saved user."
        )

    if not verb or not verb.strip():
        raise ValueError(
            "create_action() requires a non-empty verb."
        )

    if target is not None and target.pk is None:
        raise ValueError(
            "create_action() requires a saved target."
        )

    verb = verb.strip()

    duplicate_since = timezone.now() - timedelta(
        seconds=ACTION_DUPLICATE_WINDOW_SECONDS,
    )

    action_data = {
        "user_id": user.pk,
        "verb": verb,
    }

    duplicate_filters = {
        "user_id": user.pk,
        "verb": verb,
        "created__gte": duplicate_since,
    }

    if target is not None:
        target_content_type = ContentType.objects.get_for_model(
            target,
            for_concrete_model=False,
        )

        action_data.update(
            {
                "target_ct_id": target_content_type.pk,
                "target_id": target.pk,
            }
        )

        duplicate_filters.update(
            {
                "target_ct_id": target_content_type.pk,
                "target_id": target.pk,
            }
        )

    else:
        duplicate_filters.update(
            {
                "target_ct__isnull": True,
                "target_id__isnull": True,
            }
        )

    duplicate_exists = Action.objects.filter(
        **duplicate_filters,
    ).exists()

    if duplicate_exists:
        return False

    Action.objects.create(
        **action_data,
    )

    return True

