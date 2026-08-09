from django.http import Http404
from django.urls import reverse


class HideAdminFromNonStaffMiddleware:
    """
    Restrict access to the Django admin area to staff users.

    Requests targeting the admin URL from unauthenticated or non-staff users
    are rejected before reaching Django's admin views.

    This middleware is an additional access-control layer and does not replace
    Django admin's built-in authentication and permission checks.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        admin_path = reverse(
            "admin:index"
        )

        is_admin_request = (
            request.path == admin_path
            or request.path.startswith(
                f"{admin_path.rstrip('/')}/"
            )
        )

        if is_admin_request:
            user = request.user

            has_admin_access = (
                user.is_authenticated
                and (
                    user.is_staff
                    or user.is_superuser
                )
            )

            if not has_admin_access:
                raise Http404(
                    "Page not found."
                )

        return self.get_response(
            request
        )