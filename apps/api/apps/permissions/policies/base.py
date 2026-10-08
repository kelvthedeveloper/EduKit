from abc import ABC, abstractmethod
from typing import Any, Optional, Dict
from django.db.models import QuerySet, Q


class BaseScopePolicy(ABC):
    """
    Abstract base class for permission scope policies.
    Every scope (GLOBAL, ASSIGNED_CLASSES, SELF, OWN_CHILDREN, etc.) implements this policy.
    """
    scope_code: str = ''

    @abstractmethod
    def check(
        self,
        user: Any,
        permission: str,
        resource: Optional[Any] = None,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> bool:
        """
        Evaluate if user has permission on the specific resource under this scope.
        Returns True if authorized, False otherwise.
        """
        pass

    def filter_queryset(
        self,
        user: Any,
        permission: str,
        queryset: QuerySet,
        scope: Optional[Any] = None,
        scope_params: Optional[Dict[str, Any]] = None,
        **context: Any,
    ) -> QuerySet:
        """
        Filter a QuerySet to only include rows visible/actionable under this scope.
        Default implementation returns empty queryset if not overridden.
        """
        return queryset.none()
