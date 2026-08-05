from django.shortcuts import render , redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ImageCreateForm
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from action.utils import create_action

from django.db.models import Case, IntegerField, When

from .ranking import get_image_ranking
# Create your views here.


@login_required
def image_create(request):
    if request.method == 'POST':
        # form is sent
        form = ImageCreateForm(data=request.POST)
        if form.is_valid():
            # form data is valid
            cd = form.cleaned_data
            new_image = form.save(commit=False)
            # assign current user to the item
            new_image.user = request.user
            new_image.save()
            create_action(request.user, 'bookmarked image', new_image)
            messages.success(request, 'Image added successfully')
            # redirect to new created item detail view
            return redirect(new_image.get_absolute_url())
    else:
        # build form with data provided by the bookmarklet via GET
        form = ImageCreateForm(data=request.GET)
    return render(
    request,
    'images/image/create.html',
    {'section': 'images', 'form': form}
    )
    
    
from django.shortcuts import get_object_or_404
from .models import Image
def image_detail(request, id, slug):
    image = get_object_or_404(Image, id=id, slug=slug)
    total_views = r.incr(f'image:{image.id}:views')
    # increment image ranking by 1
    r.zincrby('image_ranking', 1, image.id)
    return render(
    request,
    'images/image/detail.html',
    {'section': 'images', 'image': image , 'total_views': total_views}
    )
    
    
    
    
@login_required
@require_POST
def image_like(request):
    image_id = request.POST.get("id")
    action = request.POST.get("action")

    if not image_id or action not in {"like", "unlike"}:
        return JsonResponse(
            {"status": "error", "message": "Invalid request"},
            status=400,
        )

    image = get_object_or_404(Image, id=image_id)

    if action == "like":
        already_liked = image.users_like.filter(
            id=request.user.id
        ).exists()

        if not already_liked:
            image.users_like.add(request.user)
            create_action(request.user, "likes", image)

    else:
        image.users_like.remove(request.user)

    return JsonResponse({
        "status": "ok",
        "total_likes": image.users_like.count(),
    })
    
    
    
    
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
# ...
@login_required
def image_list(request):
    images = Image.objects.all()
    paginator = Paginator(images, 8)
    page = request.GET.get('page')
    images_only = request.GET.get('images_only')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        images = paginator.page(1)
    except EmptyPage:
        if images_only:
        # If AJAX request and page out of range
        # return an empty page
            return HttpResponse('')
        # If page out of range return last page of results
        images = paginator.page(paginator.num_pages)
    if images_only:
        return render(
        request,
        'images/image/list_images.html',
        {'section': 'images', 'images': images}
        )

    return render(
    request,
    'images/image/list.html',
    {'section': 'images', 'images': images}
    )
    
    
import redis
from django.conf import settings
# connect to redis
r = redis.Redis(
 host=settings.REDIS_HOST,
 port=settings.REDIS_PORT,
 db=settings.REDIS_DB
)



@login_required
def image_ranking(request):
    image_ranking_ids = get_image_ranking(limit=10)
    
    if image_ranking_ids:
        preserved_order = Case(
            *[
                When(pk=image_id, then=position)
                for position, image_id in enumerate(image_ranking_ids)
            ],
            output_field=IntegerField(),
        )
    
        most_viewed = Image.objects.filter(
            id__in=image_ranking_ids
        ).order_by(preserved_order)
    else:
        most_viewed = Image.objects.none()