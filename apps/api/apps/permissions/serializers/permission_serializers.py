from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import Role, Permission, PermissionScope, RolePermission, RoleAssignment

User = get_user_model()


class PermissionScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermissionScope
        fields = ('uuid', 'code', 'name', 'description', 'is_system')
        read_only_fields = fields


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('uuid', 'codename', 'name', 'resource', 'action', 'description', 'is_system')
        read_only_fields = fields


class RolePermissionDetailSerializer(serializers.ModelSerializer):
    permission_codename = serializers.CharField(source='permission.codename', read_only=True)
    permission_name = serializers.CharField(source='permission.name', read_only=True)
    scope_code = serializers.CharField(source='scope.code', default='GLOBAL', read_only=True)
    scope_name = serializers.CharField(source='scope.name', default='Global', read_only=True)

    class Meta:
        model = RolePermission
        fields = (
            'uuid',
            'permission_codename',
            'permission_name',
            'scope_code',
            'scope_name',
            'scope_parameters',
        )


class RolePermissionInputSerializer(serializers.Serializer):
    permission_code = serializers.CharField(required=True)
    scope_code = serializers.CharField(required=False, default='GLOBAL')
    scope_parameters = serializers.DictField(required=False, default=dict)


class RoleSerializer(serializers.ModelSerializer):
    role_permissions = RolePermissionDetailSerializer(many=True, read_only=True)
    assigned_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = (
            'uuid',
            'code',
            'name',
            'description',
            'is_system',
            'is_active',
            'role_permissions',
            'assigned_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('uuid', 'is_system', 'created_at', 'updated_at', 'assigned_count')

    def get_assigned_count(self, obj):
        return obj.assignments.count()


class RoleCreateUpdateSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64, required=False)
    name = serializers.CharField(max_length=100, required=True)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    is_active = serializers.BooleanField(required=False, default=True)
    permissions = RolePermissionInputSerializer(many=True, required=False, default=list)

    def validate_code(self, value):
        if value:
            clean = value.strip().upper().replace(' ', '_')
            if not self.instance and Role.objects.filter(code=clean).exists():
                raise serializers.ValidationError(f'Role code "{clean}" already exists.')
            return clean
        return value


class RoleAssignmentSerializer(serializers.ModelSerializer):
    user_uuid = serializers.UUIDField(source='user.uuid', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    role_uuid = serializers.UUIDField(source='role.uuid', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    scope_override_code = serializers.CharField(source='scope_override.code', allow_null=True, read_only=True)

    class Meta:
        model = RoleAssignment
        fields = (
            'uuid',
            'user_uuid',
            'user_email',
            'user_name',
            'role_uuid',
            'role_code',
            'role_name',
            'assigned_at',
            'expires_at',
            'scope_override_code',
            'scope_context',
            'is_active',
        )
        read_only_fields = fields


class AssignRoleRequestSerializer(serializers.Serializer):
    role_code = serializers.CharField(required=False)
    role_uuid = serializers.UUIDField(required=False)
    expires_at = serializers.DateTimeField(required=False, allow_null=True, default=None)
    scope_override_code = serializers.CharField(required=False, allow_null=True, default=None)
    scope_context = serializers.DictField(required=False, default=dict)

    def validate(self, attrs):
        if not attrs.get('role_code') and not attrs.get('role_uuid'):
            raise serializers.ValidationError('Either role_code or role_uuid is required.')
        return attrs
