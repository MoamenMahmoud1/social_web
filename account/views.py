from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Exists, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from action.models import Action
from action.utils import create_action
from images.models import Image
from django.shortcuts import redirect
from .form import (
    ProfileEditForm,
    UserEditForm,
    UserRegistrationForm,
)
from .models import Contact, Profile


User = get_user_model()


@login_required
def dashboard(request):
    following_ids = list(
        request.user.following.values_list(
            "id",
            flat=True,
        )
    )

    actions = Action.objects.exclude(
        user_id=request.user.id,
    )

    if following_ids:
        actions = actions.filter(
            user_id__in=following_ids,
        )

    actions = (
        actions
        .select_related(
            "user",
            "user__profile",
            "target_ct",
        )
        .prefetch_related("target")
        .only(
            "id",
            "verb",
            "created",
            "user_id",
            "target_ct_id",
            "target_id",
            "user__id",
            "user__username",
            "user__first_name",
            "user__last_name",
            "user__profile__photo",
        )[:10]
    )

    total_images_created = request.user.images_created.count()

    return render(
        request,
        "account/dashboard.html",
        {
            "section": "dashboard",
            "actions": actions,
            "total_images_created": total_images_created,
        },
    )


def register(request):
    if request.method == "POST":
        user_form = UserRegistrationForm(
            request.POST,
        )

        if user_form.is_valid():
            with transaction.atomic():
                new_user = user_form.save(
                    commit=False,
                )

                new_user.set_password(
                    user_form.cleaned_data["password"]
                )

                new_user.save()

                Profile.objects.create(
                    user=new_user,
                )

                create_action(
                    new_user,
                    "has created an account",
                )

            return render(
                request,
                "account/register_done.html",
                {
                    "new_user": new_user,
                },
            )

    else:
        user_form = UserRegistrationForm()

    return render(
        request,
        "account/register.html",
        {
            "user_form": user_form,
        },
    )



@login_required
def edit(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
    )

    if request.method == "POST":
        user_form = UserEditForm(
            instance=request.user,
            data=request.POST,
        )

        profile_form = ProfileEditForm(
            instance=profile,
            data=request.POST,
            files=request.FILES,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            messages.success(
                request,
                "Profile updated successfully.",
            )

            return redirect("edit")

        messages.error(
            request,
            "There was an error updating your profile.",
        )

    else:
        user_form = UserEditForm(
            instance=request.user,
        )

        profile_form = ProfileEditForm(
            instance=profile,
        )

    return render(
        request,
        "account/edit.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
        },
    )



@login_required
def user_list(request):
    users = (
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
        .order_by("first_name", "last_name", "username")
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
def user_detail(request, username):
    following_exists = Contact.objects.filter(
        user_from_id=request.user.id,
        user_to_id=OuterRef("pk"),
    )

    user = get_object_or_404(
        User.objects
        .filter(is_active=True)
        .select_related("profile")
        .annotate(
            total_followers=Count(
                "rel_to_set",
                distinct=True,
            ),
            user_is_following=Exists(
                following_exists,
            ),
        )
        .only(
            "id",
            "username",
            "first_name",
            "last_name",
            "profile__photo",
        ),
        username=username,
    )

    images = (
        Image.objects
        .filter(user_id=user.id)
        .only(
            "id",
            "slug",
            "title",
            "image",
        )
    )

    return render(
        request,
        "account/user/detail.html",
        {
            "section": "people",
            "user": user,
            "images": images,
            "total_followers": user.total_followers,
            "user_is_following": user.user_is_following,
        },
    )


@login_required
@require_POST
def user_follow(request):
    user_id = request.POST.get("id")
    action = request.POST.get("action")

    if not user_id or action not in {
        "follow",
        "unfollow",
    }:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid request",
            },
            status=400,
        )

    user = get_object_or_404(
        User.objects.only(
            "id",
            "username",
        ),
        id=user_id,
        is_active=True,
    )

    if user.id == request.user.id:
        return JsonResponse(
            {
                "status": "error",
                "message": "You cannot follow yourself",
            },
            status=400,
        )

    with transaction.atomic():
        if action == "follow":
            _, created = Contact.objects.get_or_create(
                user_from_id=request.user.id,
                user_to_id=user.id,
            )

            if created:
                create_action(
                    request.user,
                    "is following",
                    user,
                )

        else:
            Contact.objects.filter(
                user_from_id=request.user.id,
                user_to_id=user.id,
            ).delete()

        total_followers = Contact.objects.filter(
            user_to_id=user.id,
        ).count()

    return JsonResponse(
        {
            "status": "ok",
            "total_followers": total_followers,
        }
    )