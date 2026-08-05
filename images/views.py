from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Case, IntegerField, Prefetch, When
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from action.utils import create_action

from .forms import ImageCreateForm
from .models import Image
from .ranking import get_image_ranking, increment_image_views


@login_required
def image_create(request):
    if request.method == "POST":
        form = ImageCreateForm(data=request.POST)

        if form.is_valid():
            image = form.save(commit=False)
            image.user = request.user
            image.save()

            create_action(
                request.user,
                "bookmarked image",
                image,
            )

            messages.success(
                request,
                "Image added successfully",
            )

            return redirect(image.get_absolute_url())

    else:
        form = ImageCreateForm(data=request.GET)

    return render(
        request,
        "images/image/create.html",
        {
            "section": "images",
            "form": form,
        },
    )


@login_required
def image_detail(request, id, slug):
    User = get_user_model()

    liked_users_queryset = (
        User.objects
        .select_related("profile")
        .only(
            "id",
            "first_name",
            "profile__photo",
        )
    )

    image = get_object_or_404(
        Image.objects
        .only(
            "id",
            "title",
            "slug",
            "image",
            "description",
        )
        .prefetch_related(
            Prefetch(
                "users_like",
                queryset=liked_users_queryset,
                to_attr="liked_users",
            )
        ),
        id=id,
        slug=slug,
    )

    total_views = increment_image_views(image.id)

    total_likes = len(image.liked_users)

    user_has_liked = any(
        user.id == request.user.id
        for user in image.liked_users
    )

    return render(
        request,
        "images/image/detail.html",
        {
            "section": "images",
            "image": image,
            "total_views": total_views,
            "total_likes": total_likes,
            "user_has_liked": user_has_liked,
        },
    )


@login_required
@require_POST
def image_like(request):
    image_id = request.POST.get("id")
    action = request.POST.get("action")

    if not image_id or action not in {"like", "unlike"}:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid request",
            },
            status=400,
        )

    image = get_object_or_404(
        Image.objects.only("id"),
        id=image_id,
    )

    likes_through_model = Image.users_like.through

    with transaction.atomic():
        if action == "like":
            _, created = likes_through_model.objects.get_or_create(
                image_id=image.id,
                user_id=request.user.id,
            )

            if created:
                create_action(
                    request.user,
                    "likes",
                    image,
                )

        else:
            likes_through_model.objects.filter(
                image_id=image.id,
                user_id=request.user.id,
            ).delete()

        total_likes = likes_through_model.objects.filter(
            image_id=image.id,
        ).count()

    return JsonResponse(
        {
            "status": "ok",
            "total_likes": total_likes,
        }
    )


@login_required
def image_list(request):
    images_queryset = Image.objects.only(
        "id",
        "slug",
        "title",
        "image",
    )

    paginator = Paginator(
        images_queryset,
        8,
    )

    page_number = request.GET.get("page")
    images_only = request.GET.get("images_only")

    try:
        images = paginator.page(page_number)

    except PageNotAnInteger:
        images = paginator.page(1)

    except EmptyPage:
        if images_only:
            return HttpResponse("")

        images = paginator.page(paginator.num_pages)

    template_name = (
        "images/image/list_images.html"
        if images_only
        else "images/image/list.html"
    )

    return render(
        request,
        template_name,
        {
            "section": "images",
            "images": images,
        },
    )


@login_required
def image_ranking(request):
    image_ranking_ids = get_image_ranking(limit=10)

    if image_ranking_ids:
        preserved_order = Case(
            *[
                When(
                    pk=image_id,
                    then=position,
                )
                for position, image_id
                in enumerate(image_ranking_ids)
            ],
            output_field=IntegerField(),
        )

        most_viewed = (
            Image.objects
            .filter(id__in=image_ranking_ids)
            .only(
                "id",
                "slug",
                "title",
            )
            .order_by(preserved_order)
        )

    else:
        most_viewed = Image.objects.none()

    return render(
        request,
        "images/image/ranking.html",
        {
            "section": "images",
            "most_viewed": most_viewed,
        },
    )