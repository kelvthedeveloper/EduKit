import re
from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    use_in_migrations = True

    @staticmethod
    def normalize_phone(identifier: str) -> str:
        digits = re.sub(r'\D', '', identifier)
        if identifier.lstrip().startswith('+') or (len(digits) >= 9 and len(digits) <= 15):
            return '+' + digits if digits else ''
        return digits

    @staticmethod
    def normalize_username(identifier: str) -> str:
        return (identifier or '').strip().lower()

    @classmethod
    def _identifier_type(cls, identifier: str) -> str:
        s = (identifier or '').strip()
        if not s:
            return 'username'
        if '@' in s:
            return 'email'
        raw_digits = re.sub(r'\D', '', s)
        if s.startswith('+'):
            if len(raw_digits) >= 7:
                return 'phone'
            return 'username'
        if s.isdigit():
            if len(s) >= 9 and len(s) <= 15:
                return 'phone'
            return 'username'
        cleaned_plus = ''.join(ch for ch in s if ch.isdigit() or ch in '+')
        if s.startswith('(') and s.endswith(')') is False and len(raw_digits) >= 9:
            return 'phone'
        if '+' in s or '(' in s or '-' in s:
            if len(raw_digits) >= 9:
                return 'phone'
            return 'username'
        return 'username'

    @classmethod
    def normalize_identifier(cls, identifier: str):
        id_type = cls._identifier_type(identifier)
        if id_type == 'email':
            return id_type, BaseUserManager.normalize_email(identifier).strip()
        if id_type == 'phone':
            return id_type, cls.normalize_phone(identifier)
        return id_type, cls.normalize_username(identifier)

    def _create_user(self, identifier: str, password=None, **extra_fields):
        if not identifier:
            raise ValueError('An identifier (email, phone or username) is required.')
        id_type, normalized = self.normalize_identifier(identifier)
        fields = {id_type: normalized, **extra_fields}
        if not fields.get('username') and id_type != 'username':
            fields['username'] = normalized
        user = self.model(**fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, identifier: str, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_system_superuser', False)
        return self._create_user(identifier, password, **extra_fields)

    def create_superuser(self, identifier: str, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_system_superuser', True)
        extra_fields.setdefault('account_status', 'ACTIVE')
        extra_fields.setdefault('email_verified', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(identifier, password, **extra_fields)

    def get_by_identifier(self, identifier: str):
        id_type, normalized = self.normalize_identifier(identifier)
        if id_type == 'email':
            lookup = {'email__iexact': normalized}
        elif id_type == 'phone':
            lookup = {'phone': normalized}
        else:
            lookup = {'username': normalized}
        try:
            return self.get(**lookup)
        except self.model.DoesNotExist:
            raise self.model.DoesNotExist(
                f'{self.model._meta.object_name} matching {id_type}={identifier!r} does not exist.'
            )
