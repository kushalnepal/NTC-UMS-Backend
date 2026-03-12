from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import LoginView, UserDetailView, SignupView, UserViewSet
from .views import HierarchyMembersView

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('hierarchy-members/', HierarchyMembersView.as_view(), name='hierarchy-members'),
     path('hierarchy-members/<uuid:user_id>/', HierarchyMembersView.as_view(), name='hierarchy-members-crud'),
   
] + router.urls


