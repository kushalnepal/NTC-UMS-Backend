from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from .models import Domain, Organization, Department, Wing, Role, Membership

User = get_user_model()


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = '__all__'

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class MemberSerializer(serializers.ModelSerializer):
    """Serializer for user members"""
    class Meta:
        model = User
        fields = ("id", "username", "email", "phone")
        read_only_fields = ("id",)


class WingSerializer(serializers.ModelSerializer):
    """Serializer for Wing with its members"""
    wing_id = serializers.UUIDField(source='id', read_only=True)
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = Wing
        fields = ('id', 'wing_id', 'name', 'members')
    
    def get_members(self, obj):
        """Get all users who are members of this wing"""
        content_type = ContentType.objects.get_for_model(Wing)
        memberships = Membership.objects.filter(
            content_type=content_type,
            object_id=obj.id
        ).select_related('user')
        return MemberSerializer([m.user for m in memberships], many=True).data


class DepartmentWithWingsSerializer(serializers.ModelSerializer):
    """Serializer for Department with its wings and members"""
    wings = WingSerializer(many=True, read_only=True)
    members = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ('id', 'name', 'wings', 'members')
    
    def get_members(self, obj):
        """Get members directly assigned to this department (not to any wing)"""
        content_type = ContentType.objects.get_for_model(Department)
        memberships = Membership.objects.filter(
            content_type=content_type,
            object_id=obj.id
        ).select_related('user')
        return MemberSerializer([m.user for m in memberships], many=True).data

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'
