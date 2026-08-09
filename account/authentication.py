from django.contrib.auth import get_user_model
User = get_user_model()


class EmailAuthBackend:
    """
    Authenticate Django users using their email address and password.

    Authentication fails when the email does not exist, when more than one
    account uses the same email address, or when the password is invalid.
    """
    def authenticate(self , request , username=None , password=None):
        
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except (User.DoesNotExist , User.MultipleObjectsReturned):
            return None
        
    def get_user(self , user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        
        
        
from . import models
def create_profile(backend, user, *args, **kwargs):
    """
        Ensure socially authenticated users have an associated Profile.

        This function is intended for the social-auth pipeline and is idempotent:
        an existing profile is reused instead of creating a duplicate.
        """
    models.Profile.objects.get_or_create(user=user)