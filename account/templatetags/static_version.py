from pathlib import Path

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static


register = template.Library()


@register.simple_tag
def versioned_static(path):
    static_url = static(path)

    if not settings.DEBUG:
        return static_url

    absolute_path = finders.find(path)

    if not absolute_path:
        return static_url

    try:
        version = int(
            Path(absolute_path).stat().st_mtime_ns
        )
    except OSError:
        return static_url

    return f"{static_url}?v={version}"
