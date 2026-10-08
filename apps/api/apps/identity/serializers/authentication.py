from rest_framework import serializers
from django.contrib.auth import get_user_model

from ..models import UserSession

User = get_user_model()


class LoginRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255, required=True,
                                      help_text='Email / phone / username / student ID / staff ID')
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    remember = serializers.BooleanField(default=False, required=False)
    device_id = serializers.CharField(max_length=128, required=False, allow_blank=True)
    device_name = serializers.CharField(max_length=255, required=False, allow_blank=True)


class LoginResponseSerializer(serializers.Serializer):
    user_uuid = serializers.UUIDField(source='uuid')
    name = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    phone = serializers.CharField(allow_null=True, allow_blank=True)
    display_name = serializers.CharField()
    account_status = serializers.CharField()
    email_verified = serializers.BooleanField()
    phone_verified = serializers.BooleanField()
    roles = serializers.SerializerMethodField()
    session_uuid = serializers.UUIDField(allow_null=True)

    def get_roles(self, obj):
        try:
            qs = obj.roles_assigned.filter(expires_at__isnull=True).select_related('role')
            return [
                {'code': ra.role.code, 'name': ra.role.name, 'uuid': str(ra.role.uuid)}
                for ra in qs
            ]
        except Exception:
            return []


class LogoutSerializer(serializers.Serializer):
    all_sessions = serializers.BooleanField(default=False, required=False,
                                           help_text='If true, revoke all sessions for current user.')


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    new_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255, required=True,
                                      help_text='Email or phone associated with the account')


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=128, required=True)
    new_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)


class SessionSerializer(serializers.ModelSerializer):
    user_uuid = serializers.UUIDField(source='user.uuid', read_only=True)

    class Meta:
        model = UserSession
        fields = (
            'uuid', 'user_uuid', 'device_id', 'device_name',
            'ip_address', 'auth_source', 'last_activity', 'expires_at',
            'revoked_at', 'created_at',
        )
        read_only_fields = fields
