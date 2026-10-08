from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from ..serializers import (
    EmailVerifyRequestSerializer,
    EmailVerifyConfirmSerializer,
    PhoneVerifyRequestSerializer,
    PhoneVerifyConfirmSerializer,
    UserMeSerializer,
)
from ..services import VerificationService
from ..permissions import IsAccountActive


class EmailVerifyRequestView(APIView):
    permission_classes = [IsAuthenticated & IsAccountActive]

    @method_decorator(ratelimit(key='user', rate='5/h', method='POST', block=False))
    def post(self, request):
        ser = EmailVerifyRequestSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        ip = request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')
        VerificationService.send_email_verification(
            user=request.user,
            email=ser.validated_data.get('email'),
            ip_address=ip, user_agent=ua,
        )
        return Response({'sent': True})


class EmailVerifyConfirmView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='20/h', method='POST', block=False))
    def post(self, request):
        from common.exceptions import ValidationError as AppValErr
        ser = EmailVerifyConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = VerificationService.verify_email(token=ser.validated_data['token'])
        except AppValErr as exc:
            return Response(
                {'error': {'code': exc.default_code, 'message': exc.detail,
                           'status': exc.status_code}},
                status=exc.status_code,
            )
        return Response(UserMeSerializer(user).data)


class PhoneVerifyRequestView(APIView):
    permission_classes = [IsAuthenticated & IsAccountActive]

    @method_decorator(ratelimit(key='user', rate='5/h', method='POST', block=False))
    def post(self, request):
        ser = PhoneVerifyRequestSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        ip = request.META.get('REMOTE_ADDR')
        ua = request.META.get('HTTP_USER_AGENT', '')
        VerificationService.send_phone_verification(
            user=request.user,
            phone=ser.validated_data.get('phone'),
            ip_address=ip, user_agent=ua,
        )
        return Response({'sent': True})


class PhoneVerifyConfirmView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='30/h', method='POST', block=False))
    def post(self, request):
        from common.exceptions import ValidationError as AppValErr
        ser = PhoneVerifyConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user = VerificationService.verify_phone(
                phone=ser.validated_data['phone'],
                code=ser.validated_data['code'],
            )
        except AppValErr as exc:
            return Response(
                {'error': {'code': exc.default_code, 'message': exc.detail,
                           'status': exc.status_code}},
                status=exc.status_code,
            )
        return Response(UserMeSerializer(user).data)
