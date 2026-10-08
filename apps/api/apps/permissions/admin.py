from django.contrib import admin
from .models import Role, Permission, PermissionScope, RolePermission, RoleAssignment


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 1
    autocomplete_fields = ('permission', 'scope')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_system', 'is_active', 'created_at')
    list_filter = ('is_system', 'is_active')
    search_fields = ('name', 'code')
    inlines = [RolePermissionInline]


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'name', 'resource', 'action', 'is_system')
    list_filter = ('resource', 'action', 'is_system')
    search_fields = ('codename', 'name', 'resource')


@admin.register(PermissionScope)
class PermissionScopeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_system')
    search_fields = ('code', 'name')


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_by', 'assigned_at', 'expires_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__email', 'user__username', 'role__name')
    autocomplete_fields = ('user', 'role')
