from django.core.paginator import Paginator
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
    following_ids = request.user.following.values_list(
        "id",
        flat=True,
    )

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

    if request.user.following.exists():
        actions = actions.filter(
            user_id__in=following_ids,
        )

    actions = actions[:10]

    total_images_created = (
        request.user.images_created.count()
    )

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
def user_detail(request, username):
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
                "message": "Invalid request.",
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

    if user.pk == request.user.pk:
        return JsonResponse(
            {
                "status": "error",
                "message": "You cannot follow yourself.",
            },
            status=400,
        )

    changed = False

    with transaction.atomic():
        if action == "follow":
            _, created = Contact.objects.get_or_create(
                user_from_id=request.user.pk,
                user_to_id=user.pk,
            )

            changed = created

            if created:
                create_action(
                    request.user,
                    "is following",
                    user,
                )

        else:
            deleted_count, _ = Contact.objects.filter(
                user_from_id=request.user.pk,
                user_to_id=user.pk,
            ).delete()

            changed = deleted_count > 0

        total_followers = Contact.objects.filter(
            user_to_id=user.pk,
        ).count()

    return JsonResponse(
        {
            "status": "ok",
            "action": action,
            "changed": changed,
            "total_followers": total_followers,
        }
    )





