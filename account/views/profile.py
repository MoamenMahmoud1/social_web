
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..form import (
    ProfileEditForm,
    UserEditForm,
)
from ..models import Profile


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

        forms_are_valid = (
            user_form.is_valid()
            and profile_form.is_valid()
        )

        if forms_are_valid:
            user_form.save()
            profile_form.save()

            messages.success(
                request,
                "Profile updated successfully.",
            )

            return redirect(
                "edit"
            )

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