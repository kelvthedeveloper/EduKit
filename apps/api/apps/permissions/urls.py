from rest_framework.routers import SimpleRouter
from django.urls import path, include

from .views import (
    RoleViewSet,
    PermissionViewSet,
    ScopeViewSet,
    UserRoleAssignmentView,
)

router = SimpleRouter()
router.register(r'roles', RoleViewSet, basename='permission-role')
router.register(r'scopes', ScopeViewSet, basename='permission-scope')
router.register(r'', PermissionViewSet, basename='permission-item')

urlpatterns = [
    path('users/<uuid:user_uuid>/roles/', UserRoleAssignmentView.as_view(), name='user-role-assignments'),
    path('users/<uuid:user_uuid>/roles/<str:role_code>/', UserRoleAssignmentView.as_view(), name='user-role-revoke'),
    path('', include(router.urls)),
]
