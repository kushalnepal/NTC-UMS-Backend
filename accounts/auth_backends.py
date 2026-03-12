from django.contrib.auth.backends import BaseBackend
from django.db.models import Q
from .models import User

class MultiIdentifierBackend(BaseBackend):
    def authenticate(self, request, identifier=None, password=None, **kwargs):
        if identifier is None or password is None:
            return None
        identifier = identifier.strip().lower()
        try:
            user = User.objects.get(
                Q(username__iexact=identifier) |
                Q(email__iexact=identifier) |
                Q(phone__iexact=identifier)
            )
        except User.DoesNotExist:
            return None
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
# 1. identifier.strip().lower()
# 2. Search user using:
#    username OR email OR phone
# 3. Check password
# 4. Generate JWT token
# 5. Return token to user