from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from organization.models import Domain, Organization, Department, Wing, Role, Membership

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "phone", "is_staff")
        read_only_fields = ("id",)


class SignupSerializer(serializers.Serializer):

    # User identifiers
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    # Password
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    # Hierarchy - Optional for admin, but will be validated against creator's organization
    department = serializers.UUIDField(required=False)
    wing = serializers.UUIDField(required=False)
    wing_name = serializers.CharField(required=False, allow_blank=True)

    # Role
    role = serializers.CharField(default="User")

    # Staff
    is_staff = serializers.BooleanField(default=False)

    # ---------------- VALIDATION ---------------- #

    def validate(self, data):
        # Get request context to access user
        request = self.context.get('request')
        
        # At least one identifier
        if not any([data.get("username"), data.get("email"), data.get("phone")]):
            raise serializers.ValidationError(
                "Provide at least one identifier (username, email, or phone)."
            )

        # Password match
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match.")

        # SECURITY: Derive organization from logged-in user's membership
        # DO NOT trust organization_id from frontend
        # Check all memberships - user might belong to multiple orgs
        creator_orgs = []
        if request and request.user:
            # Get all creator's memberships
            memberships = Membership.objects.filter(user=request.user).select_related('content_type')
            for membership in memberships:
                entity = membership.entity
                if isinstance(entity, Organization):
                    creator_orgs.append(str(entity.id))
                elif isinstance(entity, Department):
                    creator_orgs.append(str(entity.organization.id))
                elif isinstance(entity, Wing):
                    creator_orgs.append(str(entity.department.organization.id))
                elif isinstance(entity, Domain):
                    # Domain admin can create in any org under their domain
                    creator_orgs = []  # Will allow all
                    break
        
        creator_orgs = list(set(creator_orgs))  # Remove duplicates
        
        # Validate department belongs to one of creator's organizations
        dept_id = data.get("department")
        if dept_id:
            try:
                dept = Department.objects.get(id=dept_id)
                # If user has org restrictions, check if dept belongs to one of them
                if creator_orgs and str(dept.organization.id) not in creator_orgs:
                    raise serializers.ValidationError(
                        "You can only create users in your own organization."
                    )
                # Store validated department
                data['_department'] = dept
            except Department.DoesNotExist:
                raise serializers.ValidationError("Department does not exist.")

        # Validate wing belongs to creator's organization (via department)
        wing_id = data.get("wing")
        if wing_id:
            try:
                wing = Wing.objects.get(id=wing_id)
                # If user has org restrictions, check if wing belongs to one of them
                if creator_orgs and str(wing.department.organization.id) not in creator_orgs:
                    raise serializers.ValidationError(
                        "You can only create users in your own organization."
                    )
                # Store validated wing
                data['_wing'] = wing
                # Also ensure department matches
                if dept_id and str(wing.department.id) != str(dept_id):
                    raise serializers.ValidationError(
                        "Wing must belong to the specified department."
                    )
            except Wing.DoesNotExist:
                raise serializers.ValidationError("Wing does not exist.")

        # Validate role - restrict based on creator's role
        role_name = data.get("role", "User").title()
        
        # Store creator info for role validation in create()
        data['_creator_membership'] = membership
        data['_creator_orgs'] = creator_orgs
        
        if not Role.objects.filter(name__iexact=role_name).exists():
            raise serializers.ValidationError(f"Role '{role_name}' does not exist.")

        return data

    # ---------------- CREATE USER ---------------- #

    @transaction.atomic
    def create(self, validated_data):

        username = validated_data.get("username")
        email = validated_data.get("email")
        phone = validated_data.get("phone")
        password = validated_data["password"]

        identifier = username or email or phone

        # Create user
        user = User.objects.create_user(identifier, password)

        user.username = username or user.username
        user.email = email or user.email
        user.phone = phone or user.phone
        user.is_staff = validated_data.get("is_staff", False)

        user.save()

        entity = None

        # -------- ENTITY RESOLUTION -------- #
        # Use validated data from context (already verified to belong to creator's org)
        
        # Check for pre-validated department from validate()
        dept = validated_data.get('_department')
        wing = validated_data.get('_wing')
        
        if wing:
            # User belongs to a wing
            entity = wing
        elif dept:
            # User belongs to a department (no wing)
            entity = dept
            
            # If wing_name is provided, create the wing under this department
            wing_name = validated_data.get("wing_name")
            if wing_name:
                wing, _ = Wing.objects.get_or_create(
                    department=dept,
                    name=wing_name
                )
                entity = wing
        else:
            # Fallback: derive from creator's membership
            request = self.context.get('request')
            if request and request.user:
                membership = Membership.objects.filter(user=request.user).first()
                if membership:
                    entity = membership.entity

        # -------- CREATE MEMBERSHIP -------- #

        if entity:

            role_name = validated_data.get("role", "User")
            role = Role.objects.get(name__iexact=role_name)

            Membership.objects.create(
                user=user,
                role=role,
                content_type=ContentType.objects.get_for_model(entity),
                object_id=entity.id
            )

        return user


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)