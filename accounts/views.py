from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.contrib.auth import authenticate
from django.contrib.contenttypes.models import ContentType

from .serializers import LoginSerializer, UserSerializer, SignupSerializer
from .models import User

from organization.models import Domain, Organization, Department, Wing, Membership, Role


# ------------------------------------------------
# SIGNUP
# ------------------------------------------------

@method_decorator(csrf_exempt, name='dispatch')
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

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(generics.GenericAPIView):

    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):

        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"LOGIN REQUEST DATA: {request.data}")
        logger.error(f"LOGIN CONTENT TYPE: {request.content_type}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]

        logger.error(f"LOGIN IDENTIFIER: {identifier}, PASSWORD LENGTH: {len(password)}")

        user = authenticate(request, identifier=identifier, password=password)

        logger.error(f"LOGIN USER: {user}")

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

            # Collect domains from memberships - use name and handle None safely
            try:
                if isinstance(entity, Domain):
                    domains.append(str(entity.name))
                elif isinstance(entity, Organization):
                    if entity.domain:
                        domains.append(str(entity.domain.name))
                elif isinstance(entity, Department):
                    if entity.organization and entity.organization.domain:
                        domains.append(str(entity.organization.domain.name))
                elif isinstance(entity, Wing):
                    if (entity.department and 
                        entity.department.organization and 
                        entity.department.organization.domain):
                        domains.append(str(entity.department.organization.domain.name))
            except Exception as e:
                # Skip if any attribute access fails
                pass

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
            # Get all memberships of the user (they might have multiple)
            memberships = Membership.objects.filter(user=user).select_related('content_type', 'role', 'user')

            if not memberships:
                return Response({"message": "User has no hierarchy"}, status=404)

            # Build list of org IDs the user has access to (as strings for comparison)
            accessible_org_ids = set()
            accessible_domain_ids = set()
            for membership in memberships:
                entity = membership.entity
                if isinstance(entity, Domain):
                    # Domain admin can access all orgs under the domain
                    accessible_domain_ids.add(str(entity.id))
                elif isinstance(entity, Organization):
                    accessible_org_ids.add(str(entity.id))
                    accessible_domain_ids.add(str(entity.domain.id))
                elif isinstance(entity, Department):
                    accessible_org_ids.add(str(entity.organization.id))
                    accessible_domain_ids.add(str(entity.organization.domain.id))
                elif isinstance(entity, Wing):
                    accessible_org_ids.add(str(entity.department.organization.id))
                    accessible_domain_ids.add(str(entity.department.organization.domain.id))

            # Get all memberships for filtering users
            all_memberships = Membership.objects.select_related(
                "user", "role", "content_type"
            ).prefetch_related("user")

            def get_users_for_entity(entity_id, entity_type):
                """Get users at a specific hierarchy level"""
                admins = []
                users = []
                
                for m in all_memberships:
                    content_type = m.content_type.name
                    
                    if content_type == entity_type:
                        entity = m.entity
                        # Get the entity's ID based on type
                        if entity_type == "domain" and str(entity.id) == str(entity_id):
                            admins.append({
                                "user_id": str(m.user.id),
                                "username": m.user.username,
                                "role": m.role.name
                            })
                        elif entity_type == "organization" and str(entity.id) == str(entity_id):
                            if m.role.name.lower() == "admin":
                                admins.append({
                                    "user_id": str(m.user.id),
                                    "username": m.user.username,
                                    "role": m.role.name
                                })
                            else:
                                users.append({
                                    "user_id": str(m.user.id),
                                    "username": m.user.username,
                                    "role": m.role.name
                                })
                        elif entity_type == "department" and str(entity.id) == str(entity_id):
                            if m.role.name.lower() == "admin":
                                admins.append({
                                    "user_id": str(m.user.id),
                                    "username": m.user.username,
                                    "role": m.role.name
                                })
                            else:
                                users.append({
                                    "user_id": str(m.user.id),
                                    "username": m.user.username,
                                    "role": m.role.name
                                })
                        elif entity_type == "wing" and str(entity.id) == str(entity_id):
                            if m.role.name.lower() == "admin":
                                admins.append({
                                    "user_id": str(m.user.id),
                                    "username": m.user.username,
                                    "role": m.role.name
                                })
                            else:
                                users.append({
                                    "user_id": str(m.user.id),
                                    "username": m.user.username,
                                    "role": m.role.name
                                })
                
                return admins, users

            # Get all domains user has access to
            if accessible_domain_ids:
                domains = Domain.objects.filter(id__in=list(accessible_domain_ids)).prefetch_related(
                    "organizations__departments__wings"
                )
            else:
                domains = []

            # Build response in the new format
            result = []

            for domain in domains:
                domain_data = {
                    "domain_id": str(domain.id),
                    "domain_name": domain.name,
                    "organizations": []
                }

                for org in domain.organizations.all():
                    # Check if user has access to this org
                    if accessible_org_ids and str(org.id) not in accessible_org_ids:
                        continue

                    org_admins, org_users = get_users_for_entity(org.id, "organization")

                    org_data = {
                        "organization_id": str(org.id),
                        "organization_name": org.name,
                        "admins": org_admins,
                        "users": org_users,
                        "departments": []
                    }

                    for dept in org.departments.all():
                        dept_admins, dept_users = get_users_for_entity(dept.id, "department")

                        dept_data = {
                            "department_id": str(dept.id),
                            "department_name": dept.name,
                            "admins": dept_admins,
                            "users": dept_users,
                            "wings": []
                        }

                        for wing in dept.wings.all():
                            wing_admins, wing_users = get_users_for_entity(wing.id, "wing")

                            wing_data = {
                                "wing_id": str(wing.id),
                                "wing_name": wing.name,
                                "admins": wing_admins,
                                "users": wing_users
                            }
                            dept_data["wings"].append(wing_data)

                        org_data["departments"].append(dept_data)

                    domain_data["organizations"].append(org_data)

                result.append(domain_data)

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


# ========================================
# HIERARCHY VIEW - For Frontend Component
# ========================================

class HierarchyView(APIView):
    """
    Returns hierarchy based on user's access level:
    - Domain level: Returns all organizations under the domain
    - Organization level: Returns that organization with departments and wings
    - Department level: Returns that department with wings
    - Wing level: Returns that wing with users
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            # Get user's membership
            membership = Membership.objects.filter(user=user).select_related(
                'content_type', 'role', 'user'
            ).first()

            if not membership:
                return Response({"message": "User has no hierarchy"}, status=404)

            entity = membership.entity
            content_type = membership.content_type.name

            # Get all memberships for filtering users
            all_memberships = Membership.objects.select_related(
                "user", "role", "content_type"
            ).prefetch_related("user")

            def get_users_for_entity(entity_id, entity_type):
                """Get users at a specific hierarchy level"""
                admins = []
                users = []
                
                for m in all_memberships:
                    content = m.content_type.name
                    
                    if content == entity_type:
                        ent = m.entity
                        if str(ent.id) == str(entity_id):
                            user_data = {
                                "user_id": str(m.user.id),
                                "username": m.user.username,
                                "role": m.role.name
                            }
                            if m.role.name.lower() == "admin":
                                admins.append(user_data)
                            else:
                                users.append(user_data)
                
                return admins, users

            # DOMAIN LEVEL - Return all organizations under the domain
            if isinstance(entity, Domain):
                result = {
                    "hierarchy_type": "domain",
                    "domain_id": str(entity.id),
                    "domain_name": entity.name,
                    "organizations": []
                }

                orgs = Organization.objects.filter(domain=entity).prefetch_related(
                    "departments__wings"
                )

                for org in orgs:
                    org_admins, org_users = get_users_for_entity(org.id, "organization")

                    org_data = {
                        "organization_id": str(org.id),
                        "organization_name": org.name,
                        "admins": org_admins,
                        "users": org_users,
                        "departments": []
                    }

                    for dept in org.departments.all():
                        dept_admins, dept_users = get_users_for_entity(dept.id, "department")

                        dept_data = {
                            "department_id": str(dept.id),
                            "department_name": dept.name,
                            "admins": dept_admins,
                            "users": dept_users,
                            "wings": []
                        }

                        for wing in dept.wings.all():
                            wing_admins, wing_users = get_users_for_entity(wing.id, "wing")

                            wing_data = {
                                "wing_id": str(wing.id),
                                "wing_name": wing.name,
                                "admins": wing_admins,
                                "users": wing_users
                            }
                            dept_data["wings"].append(wing_data)

                        org_data["departments"].append(dept_data)

                    result["organizations"].append(org_data)

                return Response([result])

            # ORGANIZATION LEVEL - Return that organization with departments and wings
            elif isinstance(entity, Organization):
                result = {
                    "hierarchy_type": "organization",
                    "organization_id": str(entity.id),
                    "organization_name": entity.name,
                    "admins": [],
                    "users": [],
                    "departments": []
                }

                org_admins, org_users = get_users_for_entity(entity.id, "organization")
                result["admins"] = org_admins
                result["users"] = org_users

                depts = Department.objects.filter(organization=entity).prefetch_related("wings")

                for dept in depts:
                    dept_admins, dept_users = get_users_for_entity(dept.id, "department")

                    dept_data = {
                        "department_id": str(dept.id),
                        "department_name": dept.name,
                        "admins": dept_admins,
                        "users": dept_users,
                        "wings": []
                    }

                    for wing in dept.wings.all():
                        wing_admins, wing_users = get_users_for_entity(wing.id, "wing")

                        wing_data = {
                            "wing_id": str(wing.id),
                            "wing_name": wing.name,
                            "admins": wing_admins,
                            "users": wing_users
                        }
                        dept_data["wings"].append(wing_data)

                    result["departments"].append(dept_data)

                return Response(result)

            # DEPARTMENT LEVEL - Return that department with wings
            elif isinstance(entity, Department):
                result = {
                    "hierarchy_type": "department",
                    "department_id": str(entity.id),
                    "department_name": entity.name,
                    "admins": [],
                    "users": [],
                    "wings": []
                }

                dept_admins, dept_users = get_users_for_entity(entity.id, "department")
                result["admins"] = dept_admins
                result["users"] = dept_users

                wings = Wing.objects.filter(department=entity)

                for wing in wings:
                    wing_admins, wing_users = get_users_for_entity(wing.id, "wing")

                    wing_data = {
                        "wing_id": str(wing.id),
                        "wing_name": wing.name,
                        "admins": wing_admins,
                        "users": wing_users
                    }
                    result["wings"].append(wing_data)

                return Response(result)

            # WING LEVEL - Return that wing with users
            elif isinstance(entity, Wing):
                result = {
                    "hierarchy_type": "wing",
                    "wing_id": str(entity.id),
                    "wing_name": entity.name,
                    "admins": [],
                    "users": []
                }

                wing_admins, wing_users = get_users_for_entity(entity.id, "wing")
                result["admins"] = wing_admins
                result["users"] = wing_users

                return Response(result)

            else:
                return Response({"message": "Invalid hierarchy"}, status=400)

        except Exception as e:
            import traceback
            return Response({
                "message": "Error fetching hierarchy",
                "error": str(e),
                "trace": traceback.format_exc()
            }, status=500)


# ========================================
# ADMIN REQUEST VIEW - Public Signup for Admins
# ========================================

class AdminRequestView(APIView):
    """
    Public endpoint to request admin access to a department/organization.
    No authentication required.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            phone = request.data.get('phone')
            password = request.data.get('password')
            password_confirm = request.data.get('password_confirm')
            
            organization_id = request.data.get('organization')
            department_id = request.data.get('department')
            wing_id = request.data.get('wing')

            # Validation
            if not username:
                return Response({"error": "Username is required"}, status=400)
            if not password:
                return Response({"error": "Password is required"}, status=400)
            if password != password_confirm:
                return Response({"error": "Passwords do not match"}, status=400)

            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return Response({"error": "Username already exists"}, status=400)
            if email and User.objects.filter(email=email).exists():
                return Response({"error": "Email already exists"}, status=400)

            # Determine target hierarchy level
            target_level = None
            target_entity = None
            content_type = None

            if wing_id:
                try:
                    target_entity = Wing.objects.get(id=wing_id)
                    target_level = "wing"
                    content_type = ContentType.objects.get_for_model(Wing)
                    department_id = str(target_entity.department.id)
                    organization_id = str(target_entity.department.organization.id)
                except Wing.DoesNotExist:
                    return Response({"error": "Wing not found"}, status=404)
            elif department_id:
                try:
                    target_entity = Department.objects.get(id=department_id)
                    target_level = "department"
                    content_type = ContentType.objects.get_for_model(Department)
                    organization_id = str(target_entity.organization.id)
                except Department.DoesNotExist:
                    return Response({"error": "Department not found"}, status=404)
            elif organization_id:
                try:
                    target_entity = Organization.objects.get(id=organization_id)
                    target_level = "organization"
                    content_type = ContentType.objects.get_for_model(Organization)
                except Organization.DoesNotExist:
                    return Response({"error": "Organization not found"}, status=404)
            else:
                return Response({
                    "error": "Must provide organization, department, or wing ID"
                }, status=400)

            # Get or create Admin role
            role, _ = Role.objects.get_or_create(name='Admin')

            # Create user
            user = User.objects.create_user(
                identifier=username,
                password=password,
                email=email or ""
            )
            if phone:
                user.phone = phone
                user.save()

            # Create membership
            Membership.objects.create(
                user=user,
                content_type=content_type,
                object_id=str(target_entity.id),
                role=role
            )

            # Generate token
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": f"Admin created successfully for {target_level}",
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone
                },
                "hierarchy_level": target_level,
                "target": {
                    "id": str(target_entity.id),
                    "name": target_entity.name
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }, status=201)

        except Exception as e:
            import traceback
            return Response({
                "error": "Failed to create admin",
                "details": str(e),
                "trace": traceback.format_exc()
            }, status=500)