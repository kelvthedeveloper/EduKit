from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import AuditEvent
from ..serializers import AuditEventSerializer
from apps.identity.permissions import IsAccountActive


class IsAuditAdmin(permissions.BasePermission):
    """
    Ensures only authorized administrators with audit.view or system staff access can view audit logs.
    """
    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_system_superuser', False) or getattr(user, 'is_staff', False):
            return True
        try:
            from apps.permissions.services import AuthorizationService
            return AuthorizationService.can(user, 'audit.view')
        except Exception:
            return False


class AuditEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only audit event trail.
    """
    queryset = AuditEvent.objects.all().select_related('actor')
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.IsAuthenticated & IsAccountActive & IsAuditAdmin]
    lookup_field = 'uuid'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action', 'status', 'resource_type']
    search_fields = ['actor_email', 'resource_id', 'ip_address']
    ordering_fields = ['created_at', 'action']
    ordering = ['-created_at']
