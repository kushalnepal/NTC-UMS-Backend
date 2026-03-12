from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType

from .serializers import LoginSerializer, UserSerializer, SignupSerializer
from .models import User

from organization.models import Domain, Organization, Department, Wing, Membership


# ------------------------------------------------
# SIGNUP
# ------------------------------------------------

class SignupView(generics.CreateAPIView):

    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        domains = []

        for membership in user.memberships.all():

            entity = membership.entity

            if isinstance(entity, Domain):
                domains.append(str(entity.id))

            elif isinstance(entity, Organization):
                domains.append(str(entity.domain.id))

            elif isinstance(entity, Department):
                domains.append(str(entity.organization.domain.id))

            elif isinstance(entity, Wing):
                domains.append(str(entity.department.organization.domain.id))

        domains = list(set(domains))

        refresh = RefreshToken.for_user(user)
        refresh["domains"] = domains

        return Response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "expires_in": refresh.access_token.lifetime.total_seconds(),
            "message": "User created successfully"
        }, status=status.HTTP_201_CREATED)


# ------------------------------------------------
# LOGIN
# ------------------------------------------------

class LoginView(generics.GenericAPIView):

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        user = authenticate(request, identifier=identifier, password=password)

        if not user:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)

        memberships = Membership.objects.filter(user=user)

        memberships_data = []
        domains = []

        for m in memberships:

            entity = m.entity

            memberships_data.append({
                "level": entity.__class__.__name__.lower(),
                "id": str(entity.id),
                "name": entity.name,
                "role": m.role.name
            })

            # Collect domains from memberships
            if isinstance(entity, Domain):
                domains.append(str(entity.id))
            elif isinstance(entity, Organization):
                domains.append(str(entity.domain.id))
            elif isinstance(entity, Department):
                domains.append(str(entity.organization.domain.id))
            elif isinstance(entity, Wing):
                domains.append(str(entity.department.organization.domain.id))

        domains = list(set(domains))

        return Response({
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "domains": domains
            },
            "memberships": memberships_data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "expires_in": refresh.access_token.lifetime.total_seconds()
        })


# ------------------------------------------------
# USER DETAIL
# ------------------------------------------------

class UserDetailView(generics.RetrieveAPIView):

    queryset = User.objects.all()
    serializer_class = UserSerializer


# ------------------------------------------------
# USER VIEWSET
# ------------------------------------------------

class UserViewSet(viewsets.ModelViewSet):

    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):

        if self.action == "create":
            return SignupSerializer

        return UserSerializer


# ------------------------------------------------
# HIERARCHY VIEW (MAIN SYSTEM)
# ------------------------------------------------

class HierarchyMembersView(APIView):

    """
    Shows hierarchy data based on user's membership level
    Admin → CRUD
    User → Read only
    """

    permission_classes = [IsAuthenticated]

    # -------------------------------------------
    # GET → READ DATA
    # -------------------------------------------

    def get(self, request):

        try:
            user = request.user
            membership = Membership.objects.filter(user=user).first()

            if not membership:
                return Response({"message": "User has no hierarchy"}, status=404)

            entity = membership.entity

            result = {
                "domains": [],
                "organizations": [],
                "departments": [],
                "wings": [],
                "users": []
            }

            # DOMAIN LEVEL
            if isinstance(entity, Domain):

                orgs = Organization.objects.filter(domain=entity)
                depts = Department.objects.filter(organization__domain=entity)
                wings = Wing.objects.filter(department__organization__domain=entity)

            # ORGANIZATION LEVEL
            elif isinstance(entity, Organization):

                orgs = Organization.objects.filter(id=entity.id)
                depts = Department.objects.filter(organization=entity)
                wings = Wing.objects.filter(department__organization=entity)

            # DEPARTMENT LEVEL
            elif isinstance(entity, Department):

                orgs = Organization.objects.filter(id=entity.organization.id)
                depts = Department.objects.filter(id=entity.id)
                wings = Wing.objects.filter(department=entity)

            # WING LEVEL
            elif isinstance(entity, Wing):

                orgs = Organization.objects.filter(id=entity.department.organization.id)
                depts = Department.objects.filter(id=entity.department.id)
                wings = Wing.objects.filter(id=entity.id)

            else:
                return Response({"message": "Invalid hierarchy"}, status=400)

            result["organizations"] = [o.name for o in orgs]
            result["departments"] = [d.name for d in depts]
            result["wings"] = [w.name for w in wings]

            # Collect users using membership
            users = []

            for m in Membership.objects.select_related("user", "role"):

                users.append({
                    "id": str(m.user.id),
                    "username": m.user.username,
                    "email": m.user.email,
                    "phone": m.user.phone,
                    "role": m.role.name,
                    "is_staff": m.user.is_staff
                })

            result["users"] = users

            return Response(result)

        except Exception as e:
            import traceback
            return Response({
                "message": "Error fetching hierarchy",
                "error": str(e),
                "trace": traceback.format_exc()
            }, status=500)


    # -------------------------------------------
    # CREATE USER (ADMIN ONLY)
    # -------------------------------------------

    def post(self, request):

        membership = Membership.objects.filter(user=request.user).first()

        if membership.role.name.lower() != "admin":
            return Response({"message": "Only admin can create users"}, status=403)

        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User created",
                "user": UserSerializer(user).data
            })

        return Response(serializer.errors, status=400)


    # -------------------------------------------
    # UPDATE USER
    # -------------------------------------------

    def put(self, request, user_id):

        membership = Membership.objects.filter(user=request.user).first()

        if membership.role.name.lower() != "admin":
            return Response({"message": "Only admin can update users"}, status=403)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)

        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors)


    # -------------------------------------------
    # DELETE USER
    # -------------------------------------------

    def delete(self, request, user_id):

        membership = Membership.objects.filter(user=request.user).first()

        if membership.role.name.lower() != "admin":
            return Response({"message": "Only admin can delete users"}, status=403)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=404)

        user.delete()

        return Response({"message": "User deleted"})