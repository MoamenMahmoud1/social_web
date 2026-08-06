from django.shortcuts import redirect


def page_not_found(
    request,
    exception,
):
    """
    Redirect every 404 error to the dashboard.
    """

    return redirect(
        "dashboard"
    )