import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction

from common.constants import Scope
from apps.permissions.models import Role, Permission, PermissionScope
from apps.permissions.services import PermissionService, RoleService

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds system scopes, permissions, default school roles, and optional development demo users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-demo-users',
            action='store_true',
            help='Create sample development demo users. STRICTLY for local dev / testing.',
        )
        parser.add_argument(
            '--demo-password',
            type=str,
            default=None,
            help='Explicit development password for demo users (defaults to EduKitDev!2026).',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Starting EduKit Identity & Permissions Seed...'))

        # 1. Scopes
        self.stdout.write('Registering system scopes...')
        PermissionService.ensure_system_scopes()
        self.stdout.write(self.style.SUCCESS(f'OK: {PermissionScope.objects.count()} scopes registered.'))

        # 2. Permissions
        self.stdout.write('Registering granular system permissions...')
        PermissionService.ensure_system_permissions()
        self.stdout.write(self.style.SUCCESS(f'OK: {Permission.objects.count()} permissions registered.'))

        # 3. Roles
        self.stdout.write('Configuring school roles...')
        self._seed_roles()
        self.stdout.write(self.style.SUCCESS(f'OK: {Role.objects.count()} roles configured.'))

        # 4. Demo Users
        if options['with-demo-users']:
            if not settings.DEBUG and os.environ.get('ALLOW_DEMO_USERS_IN_NONDEBUG') != '1':
                raise CommandError(
                    'Refusing to create demo users when DEBUG=False. '
                    'Set ALLOW_DEMO_USERS_IN_NONDEBUG=1 explicitly for QA environments.'
                )
            if getattr(settings, 'DEPLOYMENT_MODE', '') == 'production' and not settings.DEBUG:
                raise CommandError('Cannot create demo users in production environment!')
            self.stdout.write(self.style.WARNING('\n[DEV ONLY] Creating demo users for development...'))
            password = options['demo_password'] or 'EduKitDev!2026'
            self._seed_demo_users(password)

        self.stdout.write(self.style.SUCCESS('\nEduKit Identity seed completed successfully!'))

    def _seed_roles(self):
        # 1. Super Admin
        super_admin_role, _ = Role.objects.get_or_create(
            code='SUPER_ADMIN',
            defaults={
                'name': 'Super Administrator',
                'description': 'Highest school-level administrator with global management capabilities.',
                'is_system': True,
                'is_active': True,
            },
        )
        all_perms = [{'permission_code': p.codename, 'scope_code': Scope.GLOBAL} for p in Permission.objects.all()]
        RoleService.set_role_permissions(super_admin_role, all_perms)

        # 2. School Administrator
        admin_role, _ = Role.objects.get_or_create(
            code='SCHOOL_ADMIN',
            defaults={
                'name': 'School Administrator',
                'description': 'Principal / Administrator responsible for overall school operations.',
                'is_system': True,
                'is_active': True,
            },
        )
        admin_perms = [
            {'permission_code': p.codename, 'scope_code': Scope.GLOBAL}
            for p in Permission.objects.filter(
                resource__in=['students', 'attendance', 'academics', 'results', 'website', 'identity', 'audit']
            )
        ] + [
            {'permission_code': 'roles.view', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'finance.view', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'finance.export', 'scope_code': Scope.GLOBAL},
        ]
        RoleService.set_role_permissions(admin_role, admin_perms)

        # 3. Head Teacher
        head_teacher, _ = Role.objects.get_or_create(
            code='HEAD_TEACHER',
            defaults={
                'name': 'Head Teacher',
                'description': 'Academic supervisor overseeing teachers, curriculum, and grade approvals.',
                'is_system': False,
                'is_active': True,
            },
        )
        head_teacher_perms = [
            {'permission_code': 'students.view', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'attendance.view', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'attendance.manage', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'academics.view', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'academics.manage', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'results.view', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'results.approve', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'results.publish', 'scope_code': Scope.GLOBAL},
        ]
        RoleService.set_role_permissions(head_teacher, head_teacher_perms)

        # 4. Teacher
        teacher_role, _ = Role.objects.get_or_create(
            code='TEACHER',
            defaults={
                'name': 'Teacher',
                'description': 'Classroom or subject educator with class-scoped privileges.',
                'is_system': False,
                'is_active': True,
            },
        )
        teacher_perms = [
            {'permission_code': 'students.view', 'scope_code': Scope.ASSIGNED_CLASSES},
            {'permission_code': 'attendance.view', 'scope_code': Scope.ASSIGNED_CLASSES},
            {'permission_code': 'attendance.record', 'scope_code': Scope.ASSIGNED_CLASSES},
            {'permission_code': 'results.view', 'scope_code': Scope.ASSIGNED_CLASSES},
            {'permission_code': 'results.enter', 'scope_code': Scope.ASSIGNED_CLASSES},
            {'permission_code': 'results.update', 'scope_code': Scope.ASSIGNED_CLASSES},
            {'permission_code': 'academics.view', 'scope_code': Scope.GLOBAL},
        ]
        RoleService.set_role_permissions(teacher_role, teacher_perms)

        # 5. Class Teacher
        class_teacher_role, _ = Role.objects.get_or_create(
            code='CLASS_TEACHER',
            defaults={
                'name': 'Class Teacher',
                'description': 'Primary educator for a class homeroom with attendance management.',
                'is_system': False,
                'is_active': True,
            },
        )
        class_teacher_perms = list(teacher_perms) + [
            {'permission_code': 'attendance.correct', 'scope_code': Scope.ASSIGNED_CLASSES},
            {'permission_code': 'attendance.manage', 'scope_code': Scope.ASSIGNED_CLASSES},
        ]
        RoleService.set_role_permissions(class_teacher_role, class_teacher_perms)

        # 6. Bursar / Accountant
        bursar_role, _ = Role.objects.get_or_create(
            code='BURSAR',
            defaults={
                'name': 'Bursar',
                'description': 'Chief financial officer handling fees, payments, and refunds.',
                'is_system': False,
                'is_active': True,
            },
        )
        bursar_perms = [
            {'permission_code': 'finance.view', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'finance.create_payment', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'finance.refund', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'finance.export', 'scope_code': Scope.GLOBAL},
            {'permission_code': 'students.view', 'scope_code': Scope.GLOBAL},
        ]
        RoleService.set_role_permissions(bursar_role, bursar_perms)

        # 7. Parent
        parent_role, _ = Role.objects.get_or_create(
            code='PARENT',
            defaults={
                'name': 'Parent / Guardian',
                'description': 'Student parent/guardian with access strictly limited to their own children.',
                'is_system': False,
                'is_active': True,
            },
        )
        parent_perms = [
            {'permission_code': 'students.view', 'scope_code': Scope.OWN_CHILDREN},
            {'permission_code': 'attendance.view', 'scope_code': Scope.OWN_CHILDREN},
            {'permission_code': 'results.view', 'scope_code': Scope.OWN_CHILDREN},
            {'permission_code': 'finance.view', 'scope_code': Scope.OWN_CHILDREN},
            {'permission_code': 'finance.create_payment', 'scope_code': Scope.OWN_CHILDREN},
            {'permission_code': 'website.view', 'scope_code': Scope.GLOBAL},
        ]
        RoleService.set_role_permissions(parent_role, parent_perms)

        # 8. Student
        student_role, _ = Role.objects.get_or_create(
            code='STUDENT',
            defaults={
                'name': 'Student',
                'description': 'Student with access strictly limited to their own personal academic record.',
                'is_system': False,
                'is_active': True,
            },
        )
        student_perms = [
            {'permission_code': 'students.view', 'scope_code': Scope.SELF},
            {'permission_code': 'attendance.view', 'scope_code': Scope.SELF},
            {'permission_code': 'results.view', 'scope_code': Scope.SELF},
            {'permission_code': 'website.view', 'scope_code': Scope.GLOBAL},
        ]
        RoleService.set_role_permissions(student_role, student_perms)

    def _seed_demo_users(self, password):
        demo_accounts = [
            {
                'email': 'superadmin@demo.edukit.local',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role_code': 'SUPER_ADMIN',
                'is_staff': True,
                'is_system_superuser': True,
            },
            {
                'email': 'admin@demo.edukit.local',
                'first_name': 'School',
                'last_name': 'Administrator',
                'role_code': 'SCHOOL_ADMIN',
                'is_staff': True,
                'is_system_superuser': False,
            },
            {
                'email': 'teacher@demo.edukit.local',
                'first_name': 'Demo',
                'last_name': 'Teacher',
                'role_code': 'TEACHER',
                'is_staff': False,
                'is_system_superuser': False,
            },
            {
                'email': 'parent@demo.edukit.local',
                'first_name': 'Demo',
                'last_name': 'Parent',
                'role_code': 'PARENT',
                'is_staff': False,
                'is_system_superuser': False,
            },
            {
                'email': 'student@demo.edukit.local',
                'first_name': 'Demo',
                'last_name': 'Student',
                'role_code': 'STUDENT',
                'is_staff': False,
                'is_system_superuser': False,
            },
        ]

        with transaction.atomic():
            for acc in demo_accounts:
                user, created = User.objects.get_or_create(
                    email=acc['email'],
                    defaults={
                        'first_name': acc['first_name'],
                        'last_name': acc['last_name'],
                        'display_name': f"{acc['first_name']} {acc['last_name']}",
                        'account_status': 'ACTIVE',
                        'email_verified': True,
                        'is_staff': acc['is_staff'],
                        'is_system_superuser': acc['is_system_superuser'],
                    },
                )
                user.set_password(password)
                user.save()

                role = Role.objects.filter(code=acc['role_code']).first()
                if role:
                    RoleService.assign_role(user=user, role=role)

                status_label = 'CREATED' if created else 'UPDATED'
                self.stdout.write(f'  [{status_label}] {acc["email"]} ({acc["role_code"]})')

        self.stdout.write(self.style.WARNING(
            f'\n[DEMO USERS CREATED]\nPassword for all demo accounts: {password}\n'
            'WARNING: Demo accounts are strictly for development/demo testing.\n'
        ))
