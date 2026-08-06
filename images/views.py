from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.db.models import Case, Exists, IntegerField, OuterRef, When , Q
from django.http import  JsonResponse , Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from action.utils import create_action

from .forms import ImageCreateForm
from .like_services import change_image_like
from .models import Image
from .ranking import (
    get_image_ranking,
    increment_image_views,
    remove_image_from_ranking,
)

from .pagination import (
    InvalidCursorError,
    paginate_images_by_cursor,
)

from django.template.loader import render_to_string

from django.views.decorators.csrf import ensure_csrf_cookie

@login_required
def image_create(request):
    if request.method == "POST":
        form = ImageCreateForm(
            data=request.POST,
        )

        if form.is_valid():
            image = form.save(
                commit=False,
            )

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

            return redirect(
                image.get_absolute_url()
            )

    else:
        form = ImageCreateForm(
            data=request.GET,
        )

    return render(
        request,
        "images/image/create.html",
        {
            "section": "images",
            "form": form,
        },
    )

@ensure_csrf_cookie
@login_required
def image_detail(request, id, slug):
    user_like_through_model = Image.users_like.through

    image = get_object_or_404(
        Image.objects
        .select_related(
            "user",
            "user__profile",
        )
        .annotate(
            user_has_liked=Exists(
                user_like_through_model.objects.filter(
                    image_id=OuterRef("pk"),
                    user_id=request.user.id,
                )
            )
        )
        .only(
            "id",
            "user_id",
            "user__id",
            "user__username",
            "user__first_name",
            "user__last_name",
            "user__profile__photo",
            "title",
            "slug",
            "image",
            "description",
            "total_likes",
        ),
        id=id,
        slug=slug,
    )

    liked_users = (
        image.users_like
        .select_related("profile")
        .only(
            "id",
            "username",
            "first_name",
            "last_name",
            "profile__photo",
        )
        .order_by("-id")[:12]
    )

    total_views = increment_image_views(
        image.id
    )

    return render(
        request,
        "images/image/detail.html",
        {
            "section": "images",
            "image": image,
            "liked_users": liked_users,
            "total_views": total_views,
            "total_likes": image.total_likes,
            "user_has_liked": image.user_has_liked,
        },
    )



@login_required
def image_list(request):
    images_queryset = (
        Image.objects
        .select_related(
            "user",
            "user__profile",
        )
        .only(
            "id",
            "slug",
            "title",
            "image",
            "created",
            "user__id",
            "user__username",
            "user__first_name",
            "user__last_name",
            "user__profile__photo",
        )
    )

    try:
        batch = paginate_images_by_cursor(
            images_queryset,
            cursor=request.GET.get("cursor"),
        )
    except InvalidCursorError as error:
        raise Http404(
            "Invalid or expired image cursor."
        ) from error

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        images_html = render_to_string(
            "images/image/list_images.html",
            {
                "images": batch.items,
            },
            request=request,
        )

        return JsonResponse(
            {
                "html": images_html,
                "has_next": batch.has_next,
                "next_cursor": batch.next_cursor,
            }
        )

    return render(
        request,
        "images/image/list.html",
        {
            "section": "images",
            "images": batch.items,
            "has_next": batch.has_next,
            "next_cursor": batch.next_cursor,
        },
    )

@login_required
def image_ranking(request):
    image_ranking_ids = get_image_ranking(
        limit=10
    )

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
            .filter(
                id__in=image_ranking_ids
            )
            .only(
                "id",
                "slug",
                "title",
            )
            .order_by(
                preserved_order
            )
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





@require_POST
@login_required
def image_like(request):
    image_id = request.POST.get("id")
    action = request.POST.get("action")

    if not image_id or action not in {"like", "unlike"}:
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid request.",
            },
            status=400,
        )

    image = get_object_or_404(
        Image,
        id=image_id,
    )

    result = change_image_like(
        image=image,
        user=request.user,
        action=action,
    )

    return JsonResponse(
        {
            "status": "ok",
            "action": result.action,
            "changed": result.changed,
        }
    )

@login_required
@require_POST
def image_delete(request, id):
    image = get_object_or_404(
        Image,
        id=id,
        user=request.user,
    )

    image_id = image.id

    image.delete()

    remove_image_from_ranking(
        image_id
    )

    messages.success(
        request,
        "Image deleted successfully.",
    )

    return redirect(
        "images:list"
    )