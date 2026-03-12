from django.contrib.auth.backends import BaseBackend
from django.db.models import Q
from .models import User
import logging

logger = logging.getLogger(__name__)

class MultiIdentifierBackend(BaseBackend):
    def authenticate(self, request, identifier=None, password=None, **kwargs):
        logger.error(f"AUTH BACKEND: identifier={identifier}, password_present={password is not None}")
        if identifier is None or password is None:
            return None
        identifier = identifier.strip().lower()
        logger.error(f"AUTH BACKEND: searching for {identifier}")
        try:
            user = User.objects.get(
                Q(username__iexact=identifier) |
                Q(email__iexact=identifier) |
                Q(phone__iexact=identifier)
            )
            logger.error(f"AUTH BACKEND: found user: {user.username}")
        except User.DoesNotExist:
            logger.error("AUTH BACKEND: user not found")
            return None
        if user.check_password(password) and user.is_active:
            logger.error("AUTH BACKEND: password correct, returning user")
            return user
        logger.error("AUTH BACKEND: password incorrect or user inactive")
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