from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from ..serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserMeSerializer,
    UserMeUpdateSerializer,
)
from ..services import AuthenticationService, PasswordService, SessionService
from ..permissions import IsAccountActive


class LoginThrottle(AnonRateThrottle):
    scope = 'login'


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=False))
    def post(self, request):
        from common.exceptions import AuthenticationError as AppAuthError, ValidationError as AppValErr
        from django.core.exceptions import ValidationError as DjangoValErr
        ser = LoginRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            user = AuthenticationService.authenticate(
                identifier=data['identifier'],
                password=data['password'],
                request=request,
            )
            remember = bool(data.get('remember'))
            if remember:
                request.session.set_expiry(60 * 60 * 24 * 14)  # 14 days
            user, user_session = AuthenticationService.login(
                user=user,
                request=request,
                device_meta={
                    'device_id': data.get('device_id', ''),
                    'device_name': data.get('device_name', ''),
                },
            )
        except (AppAuthError, AppValErr) as exc:
            return Response(
                {
                    'error': {
                        'code': getattr(exc, 'default_code', 'authentication_failed'),
                        'message': exc.detail,
                        'status': exc.status_code,
                    }
                },
                status=exc.status_code,
            )
        response_data = LoginResponseSerializer(user).data
        if user_session:
            response_data['session_uuid'] = str(user_session.uuid)
        return Response(response_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated & IsAccountActive]

    def post(self, request):
        ser = LogoutSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        all_sessions = ser.validated_data.get('all_sessions', False)
        current_key = getattr(request.session, 'session_key', None)
        if all_sessions:
            SessionService.revoke_all(request.user, actor=request.user, source='logout_all')
        else:
            AuthenticationService.logout(request)
        return Response({'ok': True}, status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated & IsAccountActive]

    def get(self, request):
        data = UserMeSerializer(request.user).data
        return Response(data)

    def patch(self, request):
        ser = UserMeUpdateSerializer(instance=request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(UserMeSerializer(request.user).data)


class RefreshSessionView(APIView):
    permission_classes = [IsAuthenticated & IsAccountActive]

    def post(self, request):
        user = AuthenticationService.refresh_session(request)
        return Response(UserMeSerializer(user).data)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated & IsAccountActive]

    def post(self, request):
        from common.exceptions import AuthenticationError, ValidationError as AppValErr
        ser = PasswordChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            PasswordService.change_password(
                user=request.user,
                old_password=ser.validated_data['old_password'],
                new_password=ser.validated_data['new_password'],
            )
        except AuthenticationError as exc:
            return Response({'error': {'code': exc.default_code, 'message': exc.detail,
                                       'status': exc.status_code}},
                            status=exc.status_code)
        except AppValErr as exc:
            return Response({'error': {'code': exc.default_code, 'message': exc.detail,
                                       'status': exc.status_code,
                                       'data': getattr(exc, 'data', {})}},
                            status=exc.status_code)
        AuthenticationService.logout(request)
        return Response({'ok': True, 'message': 'Password changed. Please log in again.'})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]
    throttle_scope = 'password_reset'

    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST', block=False))
    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ip = request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')
        result = PasswordService.request_reset(
            identifier=ser.validated_data['identifier'],
            ip=ip, user_agent=ua,
        )
        # Always return sent=True to avoid user enumeration attacks.
        return Response({'sent': True})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    @method_decorator(ratelimit(key='ip', rate='10/h', method='POST', block=False))
    def post(self, request):
        from common.exceptions import ValidationError as AppValErr
        ser = PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            PasswordService.confirm_reset(
                token_str=ser.validated_data['token'],
                new_password=ser.validated_data['new_password'],
            )
        except AppValErr as exc:
            return Response({'error': {'code': exc.default_code, 'message': exc.detail,
                                       'status': exc.status_code}},
                            status=exc.status_code)
        return Response({'ok': True, 'message': 'Password reset successfully.'})
