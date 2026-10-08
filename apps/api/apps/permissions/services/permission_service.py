from typing import List, Dict, Tuple
from common.constants import Action, Scope
from ..models import Permission, PermissionScope, Role


# Production registry of built-in system permissions
SYSTEM_PERMISSIONS: List[Tuple[str, str, str, str, str]] = [
    # (codename, name, resource, action, description)
    # Students
    ('students.view', 'View Students', 'students', Action.VIEW, 'View student profiles and directory.'),
    ('students.create', 'Create Students', 'students', Action.CREATE, 'Enroll new students.'),
    ('students.update', 'Update Students', 'students', Action.UPDATE, 'Update student information.'),
    ('students.archive', 'Archive Students', 'students', Action.ARCHIVE, 'Archive/deactivate students.'),

    # Attendance
    ('attendance.view', 'View Attendance', 'attendance', Action.VIEW, 'View attendance records.'),
    ('attendance.record', 'Record Attendance', 'attendance', Action.CREATE, 'Mark daily or session attendance.'),
    ('attendance.correct', 'Correct Attendance', 'attendance', Action.UPDATE, 'Modify previously recorded attendance.'),
    ('attendance.manage', 'Manage Attendance', 'attendance', Action.MANAGE, 'Administer attendance policies and reports.'),

    # Results & Assessments
    ('results.view', 'View Results', 'results', Action.VIEW, 'View term or exam marks and report cards.'),
    ('results.enter', 'Enter Results', 'results', Action.CREATE, 'Enter raw assessment scores.'),
    ('results.update', 'Update Results', 'results', Action.UPDATE, 'Edit entered marks before approval.'),
    ('results.approve', 'Approve Results', 'results', Action.APPROVE, 'Approve academic results for publishing.'),
    ('results.publish', 'Publish Results', 'results', Action.PUBLISH, 'Publish report cards to parents and students.'),

    # Academics
    ('academics.view', 'View Academics', 'academics', Action.VIEW, 'View curriculum, terms, classes, and subjects.'),
    ('academics.manage', 'Manage Academics', 'academics', Action.MANAGE, 'Configure terms, classes, timetables, and subjects.'),

    # Finance
    ('finance.view', 'View Financial Records', 'finance', Action.VIEW, 'Inspect fee structures, balances, and ledger.'),
    ('finance.create_payment', 'Record Payments', 'finance', Action.CREATE, 'Record payments and fee receipts.'),
    ('finance.refund', 'Process Refunds', 'finance', Action.UPDATE, 'Issue fee refunds and reversals.'),
    ('finance.export', 'Export Financial Data', 'finance', Action.EXPORT, 'Export financial statements and reconciliations.'),

    # Identity & Accounts
    ('identity.view', 'View User Accounts', 'identity', Action.VIEW, 'View staff, parent, and user identities.'),
    ('identity.manage', 'Manage User Accounts', 'identity', Action.MANAGE, 'Create, suspend, or update user accounts.'),

    # Roles & Permissions
    ('roles.view', 'View Roles', 'roles', Action.VIEW, 'Inspect roles and permission assignments.'),
    ('roles.manage', 'Manage Roles', 'roles', Action.MANAGE, 'Configure roles and assign user permissions.'),

    # Audit
    ('audit.view', 'View Audit Trail', 'audit', Action.VIEW, 'View immutable security and activity audit logs.'),

    # Website
    ('website.view', 'View Website Content', 'website', Action.VIEW, 'View public school portal contents.'),
    ('website.create', 'Create Website Content', 'website', Action.CREATE, 'Draft news, events, and announcements.'),
    ('website.update', 'Update Website Content', 'website', Action.UPDATE, 'Edit website content and pages.'),
    ('website.publish', 'Publish Website Content', 'website', Action.PUBLISH, 'Publish announcements and pages live.'),
]

# Standard scopes registry
SYSTEM_SCOPES: List[Tuple[str, str, str]] = [
    (Scope.GLOBAL, 'Global (All School)', 'Unrestricted access across the entire school installation.'),
    (Scope.ASSIGNED_CLASSES, 'Assigned Classes', 'Restricted to classes explicitly assigned to this teacher/staff.'),
    (Scope.ASSIGNED_SUBJECTS, 'Assigned Subjects', 'Restricted to subjects taught by this educator.'),
    (Scope.DEPARTMENT, 'Department', 'Restricted to records in the user’s academic or administrative department.'),
    (Scope.SELECTED_CLASSES, 'Selected Classes', 'Restricted to specific configured class IDs.'),
    (Scope.OWN_CHILDREN, 'Own Children', 'Restricted strictly to the user’s linked biological/legal children.'),
    (Scope.SELF, 'Self Only', 'Restricted exclusively to records belonging to the authenticated user themselves.'),
]


class PermissionService:
    @staticmethod
    def ensure_system_scopes():
        """
        Idempotently registers all system scopes.
        """
        for code, name, description in SYSTEM_SCOPES:
            PermissionScope.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': description, 'is_system': True},
            )

    @staticmethod
    def ensure_system_permissions():
        """
        Idempotently registers all system permissions.
        """
        for codename, name, resource, action, description in SYSTEM_PERMISSIONS:
            Permission.objects.update_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'resource': resource,
                    'action': action,
                    'description': description,
                    'is_system': True,
                },
            )

    @staticmethod
    def get_all_registered():
        return Permission.objects.all().order_by('resource', 'action')
