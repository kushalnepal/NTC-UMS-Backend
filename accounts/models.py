import uuid
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager
)
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    def _create_user(self, identifier, password, **extra_fields):
        if not identifier:
            raise ValueError('The given identifier must be set')
        identifier = identifier.strip().lower()
        user = self.model(
            **extra_fields,
            **self.normalize_identifier(identifier)
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def normalize_identifier(self, identifier):
        data = {}
        if '@' in identifier:
            data['email'] = identifier
        elif identifier.isdigit():
            data['phone'] = identifier
        else:
            data['username'] = identifier
        return data

    def create_user(self, identifier, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        return self._create_user(identifier, password, **extra_fields)

    def create_superuser(self, identifier, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(identifier, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id        = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username  = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email     = models.EmailField(unique=True, null=True, blank=True)
    phone     = models.CharField(max_length=20, unique=True, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'username'  # overridden by backend
    REQUIRED_FIELDS = []

    objects = UserManager()

    def clean(self):
        super().clean()
        if not (self.username or self.email or self.phone):
            raise ValidationError('User must have a username, email or phone.')

    def __str__(self):
        return self.email or self.username or self.phone
