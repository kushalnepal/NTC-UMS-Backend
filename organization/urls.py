from rest_framework.routers import DefaultRouter
from .views import (
    DomainViewSet, OrganizationViewSet, DepartmentViewSet,
    WingViewSet, RoleViewSet, MembershipViewSet
)

router = DefaultRouter()
router.register('domains', DomainViewSet)
router.register('organizations', OrganizationViewSet)
router.register('departments', DepartmentViewSet)
router.register('wings', WingViewSet)
router.register('roles', RoleViewSet)
router.register('memberships', MembershipViewSet)

urlpatterns = router.urls
