from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from ..models import UserSession
from ..serializers import SessionSerializer
from ..services import SessionService
from ..permissions import IsAccountActive
from ..selectors import session_list_active


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated & IsAccountActive]
    lookup_field = 'uuid'

    def get_queryset(self):
        return session_list_active(self.request.user)

    def destroy(self, request, uuid=None):
        s = SessionService.revoke_by_uuid(uuid, actor=request.user, source='user_api')
        if not s:
            return Response({'error': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='revoke-others')
    def revoke_others(self, request):
        current_key = getattr(request.session, 'session_key', None)
        n = SessionService.revoke_all_other(request.user, current_key, actor=request.user,
                                             source='revoke_others_api')
        return Response({'revoked': n})
