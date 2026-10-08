from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMeSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    effective_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'uuid', 'email', 'phone', 'username', 'first_name', 'last_name',
            'display_name', 'name', 'full_name', 'account_status',
            'email_verified', 'phone_verified', 'is_staff',
            'last_login', 'last_active', 'created_at', 'updated_at',
            'roles', 'effective_permissions',
        )
        read_only_fields = (
            'uuid', 'account_status', 'is_staff', 'last_login', 'last_active',
            'created_at', 'updated_at', 'roles', 'effective_permissions',
        )

    def get_roles(self, obj):
        try:
            return [
                {'code': ra.role.code, 'name': ra.role.name, 'uuid': str(ra.role.uuid)}
                for ra in obj.roles_assigned.filter(expires_at__isnull=True).select_related('role')
            ]
        except Exception:
            return []

    def get_effective_permissions(self, obj):
        try:
            from apps.permissions.services import AuthorizationService
            perms = AuthorizationService.get_effective_permissions(obj)
            return sorted(perms.keys())
        except Exception:
            return []


class UserMeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'display_name')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'uuid', 'email', 'phone', 'username', 'first_name', 'last_name',
            'display_name', 'name', 'account_status', 'email_verified',
            'phone_verified', 'is_staff', 'last_login', 'last_active',
            'created_at', 'updated_at',
        )
        read_only_fields = fields
