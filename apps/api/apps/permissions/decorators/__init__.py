from functools import wraps
from typing import Optional
from common.exceptions import AuthorizationError
from ..services import AuthorizationService


def require_permission(permission_codename: str):
    """
    Decorator to enforce scoped authorization on view functions or methods.
    Raises AuthorizationError (HTTP 403) if authorization fails.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            request = None
            for arg in args:
                if hasattr(arg, 'user'):
                    request = arg
                    break
            user = getattr(request, 'user', None) if request else None

            if not user or not user.is_authenticated:
                raise AuthorizationError(detail='Authentication required.', code='not_authenticated', status_code=401)

            if not AuthorizationService.can(user, permission_codename):
                raise AuthorizationError(
                    detail=f'Permission denied: required capability "{permission_codename}".',
                    code='permission_denied',
                )

            return view_func(*args, **kwargs)
        return _wrapped_view
    return decorator


__all__ = ['require_permission']
