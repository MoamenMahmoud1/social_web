
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from action.utils import create_action

from ..form import UserRegistrationForm


AUTH_TEMPLATE = "account/auth.html"


class AccountLoginView(LoginView):
    template_name = AUTH_TEMPLATE
    redirect_authenticated_user = True

    def get_context_data(
        self,
        **kwargs,
    ):
        context = super().get_context_data(
            **kwargs
        )

        context.update(
            {
                "active_panel": "login",
                "login_form": context[
                    "form"
                ],
                "signup_form": (
                    UserRegistrationForm()
                ),
            }
        )

        return context

    def form_valid(
        self,
        form,
    ):
        messages.success(
            self.request,
            "Welcome back.",
        )

        return super().form_valid(
            form
        )


@require_http_methods(
    [
        "GET",
        "POST",
    ]
)
def register(request):
    if request.user.is_authenticated:
        return redirect(
            "dashboard"
        )

    signup_form = UserRegistrationForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and signup_form.is_valid()
    ):
        with transaction.atomic():
            new_user = signup_form.save(
                commit=False
            )

            new_user.set_password(
                signup_form.cleaned_data[
                    "password"
                ]
            )

            new_user.save()

            create_action(
                new_user,
                "has created an account",
            )

        login(
            request,
            new_user,
            backend=(
                "django.contrib.auth.backends."
                "ModelBackend"
            ),
        )

        messages.success(
            request,
            "Your account was created successfully.",
        )

        return redirect(
            "dashboard"
        )

    return render(
        request,
        AUTH_TEMPLATE,
        {
            "active_panel": "signup",
            "login_form": AuthenticationForm(
                request=request
            ),
            "signup_form": signup_form,
        },
    )