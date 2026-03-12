from rest_framework import permissions
from django.contrib.contenttypes.models import ContentType
from organization.models import Membership
from rest_framework.permissions import BasePermission
class IsScopedAdmin(permissions.BasePermission):
    """
    Checks whether the user has a membership with a given permission
    on the target object or any of its ancestors.
    Views using this class must set `required_permission` attribute.
    """

    def has_permission(self, request, view):
        perm = getattr(view, 'required_permission', None)
        if perm is None:
            return True
        obj = None
        if hasattr(view, 'get_object'):
            try:
                obj = view.get_object()
            except Exception:
                obj = None
        return self._check_perm(request.user, obj, perm)

    def _check_perm(self, user, obj, perm):
        if obj is None or not user.is_authenticated:
            return False
        current = obj
        while current is not None:
            ctype = ContentType.objects.get_for_model(current)
            if Membership.objects.filter(
                user=user,
                content_type=ctype,
                object_id=current.pk,
                role__permissions__contains=[perm],
            ).exists():
                return True
            # try to get parent attribute generically
            current = getattr(current, 'parent', None)
        return False




class IsHierarchyAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):

        if request.method in ['GET']:
            return True

        membership = Membership.objects.filter(user=request.user).first()

        if not membership:
            return False

        role = membership.role.name.lower()

        return role in ["admin", "manager"]