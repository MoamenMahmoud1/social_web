from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from action.models import Action


@login_required
def dashboard(request):
    actions = (
        Action.objects
        .exclude(user=request.user)
        .select_related(
            "user",
            "user__profile",
        )
        .prefetch_related("target")
        .order_by("-created")
    )

    following_ids = request.user.following.values_list(
        "id",
        flat=True,
    )

    if following_ids.exists():
        actions = actions.filter(
            user_id__in=following_ids,
        )

    context = {
        "section": "dashboard",
        "actions": actions[:10],
        "total_images_created": (
            request.user.images_created.count()
        ),
    }

    return render(
        request,
        "account/dashboard.html",
        context,
    )