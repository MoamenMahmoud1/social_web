
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(
    post_save,
    sender=settings.AUTH_USER_MODEL,
)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a profile automatically when a new user account is created.

    The signal guarantees that application users have an associated Profile
    object immediately after successful account creation.
    """

    if created:
        Profile.objects.get_or_create(
            user=instance,
        )

