import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Domain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    @property
    def parent(self):
        # domain is the root, has no parent
        return None

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(Domain, on_delete=models.PROTECT, related_name='organizations')
    name   = models.CharField(max_length=255)

    class Meta:
        unique_together = ('domain', 'name')

    def __str__(self):
        return f"{self.name} ({self.domain})"

    @property
    def parent(self):
        return self.domain

class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='departments')
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('organization', 'name')

    def __str__(self):
        return f"{self.name} ({self.organization})"

    @property
    def parent(self):
        return self.organization

class Wing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='wings')
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('department', 'name')

    def clean(self):
        super().clean()
        # additional integrity checks can go here

    def __str__(self):
        return f"{self.name} ({self.department})"

    @property
    def parent(self):
        return self.department

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.JSONField(default=list)

    def __str__(self):
        return self.name

class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='memberships')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    entity = GenericForeignKey('content_type', 'object_id')
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"{self.user} → {self.role} @ {self.entity}"
