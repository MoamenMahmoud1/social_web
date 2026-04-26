from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.



class Action(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL , on_delete=models.CASCADE)
    verb = models.CharField(max_length=255)
    target_ct = models.ForeignKey(ContentType , null=True , blank=True , related_name="target_obj",on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(null=True , blank=True)
    target = GenericForeignKey("target_ct" , "target_id")
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['-created']),
            
        ]
        ordering = ['-created']

