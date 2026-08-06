from django.http import Http404
from django.urls import reverse


class HideAdminFromNonStaffMiddleware:
    """
    Hide the Django admin from users who are not staff.

    Staff members and superusers continue to access the
    admin normally. Other users receive a real 404 response.
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