import logging

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Image
from .ranking import remove_image_from_ranking


logger = logging.getLogger(__name__)


@receiver(
    post_delete,
    sender=Image,
    dispatch_uid="images.cleanup_deleted_image",
)
def cleanup_deleted_image(
    sender,
    instance,
    **kwargs,
):
    """
    Clean external resources after an image is deleted.

    Database relations are handled by Django.
    The storage file and Redis ranking are cleaned
    only after the database transaction commits.
    """

    image_id = instance.pk
    image_name = instance.image.name
    image_storage = instance.image.storage

    def cleanup_external_resources():
        remove_image_from_ranking(
            image_id
        )

        if not image_name:
            return

        try:
            image_storage.delete(
                image_name
            )
        except OSError:
            logger.exception(
                "Could not delete stored file for image %s",
                image_id,
            )

    transaction.on_commit(
        cleanup_external_resources
    )



