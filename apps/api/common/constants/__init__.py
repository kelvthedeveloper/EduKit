AUTH_SOURCE_PASSWORD = 'password'
AUTH_SOURCE_TOKEN = 'token'
AUTH_SOURCE_SSO = 'sso'
AUTH_SOURCE_NFC = 'nfc'
AUTH_SOURCE_APIKEY = 'api_key'

AUTH_SOURCES = (
    (AUTH_SOURCE_PASSWORD, 'Password'),
    (AUTH_SOURCE_TOKEN, 'Token'),
    (AUTH_SOURCE_SSO, 'SSO'),
    (AUTH_SOURCE_NFC, 'NFC Badge'),
    (AUTH_SOURCE_APIKEY, 'API Key'),
)


class AccountStatus:
    PENDING_VERIFICATION = 'PENDING_VERIFICATION'
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    SUSPENDED = 'SUSPENDED'

    CHOICES = (
        (PENDING_VERIFICATION, 'Pending Verification'),
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (SUSPENDED, 'Suspended'),
    )

    AUTH_ALLOWED = {ACTIVE}


class Action:
    VIEW = 'VIEW'
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    ARCHIVE = 'ARCHIVE'
    EXPORT = 'EXPORT'
    APPROVE = 'APPROVE'
    PUBLISH = 'PUBLISH'
    MANAGE = 'MANAGE'

    CHOICES = (
        (VIEW, 'View'),
        (CREATE, 'Create'),
        (UPDATE, 'Update'),
        (DELETE, 'Delete'),
        (ARCHIVE, 'Archive'),
        (EXPORT, 'Export'),
        (APPROVE, 'Approval'),
        (PUBLISH, 'Publish'),
        (MANAGE, 'Manage'),
    )
    ALL = [VIEW, CREATE, UPDATE, DELETE, ARCHIVE, EXPORT, APPROVE, PUBLISH, MANAGE]


class Scope:
    GLOBAL = 'GLOBAL'
    ASSIGNED_CLASSES = 'ASSIGNED_CLASSES'
    ASSIGNED_SUBJECTS = 'ASSIGNED_SUBJECTS'
    DEPARTMENT = 'DEPARTMENT'
    SELECTED_CLASSES = 'SELECTED_CLASSES'
    OWN_CHILDREN = 'OWN_CHILDREN'
    SELF = 'SELF'

    CHOICES = (
        (GLOBAL, 'Global (All)'),
        (ASSIGNED_CLASSES, 'Assigned Classes'),
        (ASSIGNED_SUBJECTS, 'Assigned Subjects'),
        (DEPARTMENT, 'Department'),
        (SELECTED_CLASSES, 'Selected Classes'),
        (OWN_CHILDREN, 'Own Children'),
        (SELF, 'Self Only'),
    )
    SYSTEM_DEFINED = [GLOBAL, ASSIGNED_CLASSES, ASSIGNED_SUBJECTS, DEPARTMENT, SELECTED_CLASSES, OWN_CHILDREN, SELF]


class AuditAction:
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILED = 'LOGIN_FAILED'
    LOGOUT = 'LOGOUT'
    SESSION_REVOKED = 'SESSION_REVOKED'
    PASSWORD_CHANGED = 'PASSWORD_CHANGED'
    PASSWORD_RESET_REQUESTED = 'PASSWORD_RESET_REQUESTED'
    PASSWORD_RESET_COMPLETED = 'PASSWORD_RESET_COMPLETED'
    ACCOUNT_VERIFIED = 'ACCOUNT_VERIFIED'
    ACCOUNT_ACTIVATED = 'ACCOUNT_ACTIVATED'
    ACCOUNT_DEACTIVATED = 'ACCOUNT_DEACTIVATED'
    ACCOUNT_LOCKED = 'ACCOUNT_LOCKED'
    ROLE_ASSIGNED = 'ROLE_ASSIGNED'
    ROLE_REMOVED = 'ROLE_REMOVED'
    ROLE_CREATED = 'ROLE_CREATED'
    ROLE_UPDATED = 'ROLE_UPDATED'
    ROLE_DELETED = 'ROLE_DELETED'
    PERMISSION_CHANGED = 'PERMISSION_CHANGED'

    CHOICES = (
        (LOGIN_SUCCESS, 'Login Success'),
        (LOGIN_FAILED, 'Login Failed'),
        (LOGOUT, 'Logout'),
        (SESSION_REVOKED, 'Session Revoked'),
        (PASSWORD_CHANGED, 'Password Changed'),
        (PASSWORD_RESET_REQUESTED, 'Password Reset Requested'),
        (PASSWORD_RESET_COMPLETED, 'Password Reset Completed'),
        (ACCOUNT_VERIFIED, 'Account Verified'),
        (ACCOUNT_ACTIVATED, 'Account Activated'),
        (ACCOUNT_DEACTIVATED, 'Account Deactivated'),
        (ACCOUNT_LOCKED, 'Account Locked'),
        (ROLE_ASSIGNED, 'Role Assigned'),
        (ROLE_REMOVED, 'Role Removed'),
        (ROLE_CREATED, 'Role Created'),
        (ROLE_UPDATED, 'Role Updated'),
        (ROLE_DELETED, 'Role Deleted'),
        (PERMISSION_CHANGED, 'Permission Changed'),
    )
    ALL = [a[0] for a in CHOICES]


AUDIT_SENSITIVE_KEYS = {
    'password', 'token', 'access_token', 'refresh_token',
    'secret', 'secret_key', 'api_key', 'private_key', 'authorization',
    'session_key', 'cookie', 'csrf', 'jwt',
}


SCOPE_RESTRICTIVENESS = {
    Scope.GLOBAL: 1,
    Scope.DEPARTMENT: 2,
    Scope.ASSIGNED_SUBJECTS: 3,
    Scope.ASSIGNED_CLASSES: 4,
    Scope.SELECTED_CLASSES: 5,
    Scope.OWN_CHILDREN: 6,
    Scope.SELF: 7,
}
"""
Higher number = more restrictive (narrower scope).
Rule: a scope_override can only NARROW the effective scope or keep it equal;
it may never WIDEN (i.e., lower restrictiveness number).
"""

DEFAULT_MAX_LOGIN_ATTEMPTS = 5
DEFAULT_ACCOUNT_LOCKOUT_DURATION_MINUTES = 30

DEPLOYMENT_SOURCE_CLOUD = 'cloud'
DEPLOYMENT_SOURCE_SCHOOL = 'school-server'
DEPLOYMENT_SOURCES = (
    (DEPLOYMENT_SOURCE_CLOUD, 'Cloud'),
    (DEPLOYMENT_SOURCE_SCHOOL, 'School Server'),
)
