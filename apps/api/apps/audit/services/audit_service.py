import logging
from typing import Optional, Any, Dict
from django.db import models

from common.constants import AUDIT_SENSITIVE_KEYS
from ..models import AuditEvent

logger = logging.getLogger('apps.audit')


class AuditService:
    @staticmethod
    def sanitize(data: Any) -> Any:
        """
        Recursively sanitizes dictionary or list data to remove sensitive keys.
        Never stores passwords, tokens, session keys, or secrets.
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, val in data.items():
                lower_k = str(key).lower()
                if any(sensitive in lower_k for sensitive in AUDIT_SENSITIVE_KEYS):
                    sanitized[key] = '[REDACTED]'
                elif isinstance(val, (dict, list)):
                    sanitized[key] = AuditService.sanitize(val)
                elif hasattr(val, 'uuid'):
                    sanitized[key] = str(val.uuid)
                elif isinstance(val, (str, int, float, bool)) or val is None:
                    sanitized[key] = val
                else:
                    sanitized[key] = str(val)
            return sanitized
        elif isinstance(data, (list, tuple)):
            return [AuditService.sanitize(item) for item in data]
        return data

    @staticmethod
    def log(
        action: str,
        actor: Optional[Any] = None,
        resource_type: str = '',
        resource_id: str = '',
        ip_address: Optional[str] = None,
        user_agent: str = '',
        status: str = 'SUCCESS',
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[AuditEvent]:
        try:
            sanitized_details = AuditService.sanitize(details or {})
            
            # Extract IP from actor or request if attached
            if not ip_address and actor and hasattr(actor, '_ip'):
                ip_address = actor._ip

            return AuditEvent.objects.create(
                actor=actor if (actor and getattr(actor, 'is_authenticated', False)) else None,
                actor_email=getattr(actor, 'email', '') or getattr(actor, 'username', '') if actor else '',
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else '',
                status=status,
                ip_address=ip_address,
                user_agent=user_agent[:1000] if user_agent else '',
                details=sanitized_details,
            )
        except Exception as exc:
            logger.error('Failed to write audit event for action %s: %s', action, exc, exc_info=True)
            return None

    @staticmethod
    def log_security(
        action: str,
        actor: Optional[Any] = None,
        entity: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: str = '',
        status: str = 'SUCCESS',
        extra: Optional[Dict[str, Any]] = None,
    ) -> Optional[AuditEvent]:
        resource_type = entity.__class__.__name__ if entity else ''
        resource_id = str(getattr(entity, 'uuid', getattr(entity, 'pk', ''))) if entity else ''
        details = extra or {}
        return AuditService.log(
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            details=details,
        )
