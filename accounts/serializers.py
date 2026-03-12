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

    # Hierarchy
    domain = serializers.UUIDField(required=False)
    organization = serializers.UUIDField(required=False)
    department = serializers.UUIDField(required=False)

    wing_name = serializers.CharField(required=False, allow_blank=True)

    # Role
    role = serializers.CharField(default="User")

    # Staff
    is_staff = serializers.BooleanField(default=False)

    # ---------------- VALIDATION ---------------- #

    def validate(self, data):

        # At least one identifier
        if not any([data.get("username"), data.get("email"), data.get("phone")]):
            raise serializers.ValidationError(
                "Provide at least one identifier (username, email, or phone)."
            )

        # Password match
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError("Passwords do not match.")

        # Validate domain
        domain_id = data.get("domain")
        if domain_id and not Domain.objects.filter(id=domain_id).exists():
            raise serializers.ValidationError("Domain does not exist.")

        # Validate organization
        org_id = data.get("organization")
        if org_id and not Organization.objects.filter(id=org_id).exists():
            raise serializers.ValidationError("Organization does not exist.")

        # Validate department
        dept_id = data.get("department")
        if dept_id and not Department.objects.filter(id=dept_id).exists():
            raise serializers.ValidationError("Department does not exist.")

        # Validate role
        role_name = data.get("role", "User")
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

        department_id = validated_data.get("department")
        organization_id = validated_data.get("organization")
        domain_id = validated_data.get("domain")

        if department_id:

            dept = Department.objects.get(id=department_id)
            entity = dept

            wing_name = validated_data.get("wing_name")

            if wing_name:
                wing, _ = Wing.objects.get_or_create(
                    department=dept,
                    name=wing_name
                )
                entity = wing

        elif organization_id:
            entity = Organization.objects.get(id=organization_id)

        elif domain_id:
            entity = Domain.objects.get(id=domain_id)

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