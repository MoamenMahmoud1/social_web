from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from action.utils import create_action

from ..models import Contact


User = get_user_model()


def error_response(
    message,
    *,
    status=400,
):
    return JsonResponse(
        {
            "status": "error",
            "message": message,
        },
        status=status,
    )


@login_required
@require_POST
def user_follow(request):
    user_id = request.POST.get("id")
    action = request.POST.get("action")

    if (
        not user_id
        or action not in {
            "follow",
            "unfollow",
        }
    ):
        return error_response(
            "Invalid request."
        )

    user = get_object_or_404(
        User.objects.only(
            "id",
            "username",
        ),
        id=user_id,
        is_active=True,
    )

    if user.pk == request.user.pk:
        return error_response(
            "You cannot follow yourself."
        )

    with transaction.atomic():
        if action == "follow":
            _, changed = (
                Contact.objects.get_or_create(
                    user_from_id=request.user.pk,
                    user_to_id=user.pk,
                )
            )

            if changed:
                create_action(
                    request.user,
                    "is following",
                    user,
                )

        else:
            deleted_count, _ = (
                Contact.objects.filter(
                    user_from_id=request.user.pk,
                    user_to_id=user.pk,
                )
                .delete()
            )

            changed = deleted_count > 0

        total_followers = (
            Contact.objects
            .filter(
                user_to_id=user.pk,
            )
            .count()
        )

    return JsonResponse(
        {
            "status": "ok",
            "action": action,
            "changed": changed,
            "total_followers": total_followers,
        }
    )