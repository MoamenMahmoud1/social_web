from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, render

from images.models import Image

from ..models import Contact


User = get_user_model()


@login_required
def user_list(request):
    users_queryset = (
        User.objects
        .filter(is_active=True)
        .select_related("profile")
        .only(
            "id",
            "username",
            "first_name",
            "last_name",
            "profile__photo",
        )
        .order_by("username")
    )

    paginator = Paginator(
        users_queryset,
        20,
    )

    users = paginator.get_page(
        request.GET.get("page"),
    )

    return render(
        request,
        "account/user/list.html",
        {
            "section": "people",
            "users": users,
        },
    )


@login_required
def user_detail(
    request,
    username,
):
    user = get_object_or_404(
        User.objects
        .filter(is_active=True)
        .select_related("profile")
        .annotate(
            total_followers=Count(
                "followers",
                distinct=True,
            ),
            is_followed_by_request_user=Exists(
                Contact.objects.filter(
                    user_from=request.user,
                    user_to=OuterRef("pk"),
                )
            ),
        ),
        username=username,
    )

    images_queryset = (
        Image.objects
        .filter(user_id=user.id)
        .only(
            "id",
            "slug",
            "title",
            "image",
            "created",
        )
        .order_by("-created")
    )

    paginator = Paginator(
        images_queryset,
        12,
    )

    images = paginator.get_page(
        request.GET.get("page"),
    )

    return render(
        request,
        "account/user/detail.html",
        {
            "section": "people",
            "user": user,
            "images": images,
        },
    )