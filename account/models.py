from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# Create your models here.


class Profile(models.Model):
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL , on_delete=models.CASCADE)
    date_of_birth = models.DateField(blank=True, null=True)
    photo = models.ImageField(upload_to='users/%Y/%m/%d', blank=True)
    
    def __str__(self):
        return 'Profile for user {}'.format(self.user.username)
    
    
    
    
class Contact(models.Model):
    user_from = models.ForeignKey(settings.AUTH_USER_MODEL , related_name='rel_from_set' , on_delete=models.CASCADE)
    user_to = models.ForeignKey(settings.AUTH_USER_MODEL , related_name='rel_to_set' , on_delete=models.CASCADE)
    
    created = models.DateTimeField(auto_now_add=True)
    
    
    class Meta:
        indexes = [
            models.Index(fields=['-created'])
        ]
        ordering = ['-created']
        
        constraints =[ models.CheckConstraint(
            check=~models.Q(user_from=models.F("user_to")),
            name="prevent_self_follow"
            
        ) ]
        
        
    def __str__(self):
        return f'{self.user_from} follows {self.user_to}'
    
    def clean(self):
        if self.user_from == self.user_to:
            raise ValidationError("You cannot follow your self")
    
    
from django.contrib.auth import get_user_model
# ...
# Add the following field to User dynamically
user_model = get_user_model()
user_model.add_to_class(
    'following',
    models.ManyToManyField(
    'self',
    through=Contact,
    related_name='followers',
    symmetrical=False
    )
)
    
    
