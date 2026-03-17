from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from .models import Domain, Organization, Department, Wing, Role, Membership
from .serializers import (
    DomainSerializer, OrganizationSerializer, DepartmentSerializer,
    WingSerializer, RoleSerializer, MembershipSerializer,
    DepartmentWithWingsSerializer
)

User = get_user_model()


class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = [permissions.AllowAny]

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.AllowAny]

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list' and self.request.query_params.get('include_wings') == 'true':
            return DepartmentWithWingsSerializer
        return DepartmentSerializer
    
    @action(detail=True, methods=['get'])
    def hierarchy(self, request, pk=None):
        """
        Get department hierarchy with wings and their members.
        Returns department with all wings and members grouped by wing.
        """
        department = self.get_object()
        serializer = DepartmentWithWingsSerializer(department)
        return Response(serializer.data)

class WingViewSet(viewsets.ModelViewSet):
    queryset = Wing.objects.all()
    serializer_class = WingSerializer
    permission_classes = [permissions.AllowAny]

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAdminUser]

class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [permissions.AllowAny]
