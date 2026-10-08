from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import (
    User, UserSession, EmailVerificationToken, PhoneVerificationCode, PasswordResetToken,
)


@admin.register(User)
class EduKitUserAdmin(BaseUserAdmin):
    list_display = ('__str__', 'account_status', 'is_staff', 'is_system_superuser',
                  'email_verified', 'phone_verified', 'last_active', 'created_at')
    list_filter = ('account_status', 'is_staff', 'is_system_superuser',
                   'email_verified', 'phone_verified', 'created_at')
    search_fields = ('=uuid', 'email', 'phone', 'username', 'first_name', 'last_name', 'display_name')
    ordering = ('-created_at',)
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'last_login', 'last_active',
                     'failed_login_attempts', 'locked_until')
    fieldsets = (
        (None, {'fields': ('uuid', 'email', 'phone', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'display_name')}),
        (_('Status'), {'fields': ('account_status', 'email_verified', 'phone_verified',
                                  'locked_until', 'failed_login_attempts')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_superuser', 'is_system_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'last_active', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'auth_source', 'ip_address', 'device_name',
                    'last_activity', 'is_active')
    list_filter = ('auth_source', 'revoked_at')
    search_fields = ('=user__uuid', '=session_key', 'device_id', 'ip_address')
    readonly_fields = ('uuid', 'session_key', 'refresh_token_jti',
                      'last_activity', 'created_at', 'updated_at')
    exclude = ()


class _TokenAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'identifier', 'expires_at', 'consumed_at')
    list_filter = ('consumed_at',)
    search_fields = ('=token', 'identifier', '=user__uuid')
    readonly_fields = ('uuid', 'token', 'created_at', 'updated_at')


admin.site.register(EmailVerificationToken, _TokenAdmin)
admin.site.register(PhoneVerificationCode, _TokenAdmin)
admin.site.register(PasswordResetToken, _TokenAdmin)
