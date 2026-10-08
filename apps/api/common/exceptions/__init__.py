from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status
from django.http import JsonResponse


class BaseAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred.'
    default_code = 'error'

    def __init__(self, detail=None, code=None, status_code=None, data=None):
        super().__init__(detail=detail, code=code)
        if status_code is not None:
            self.status_code = status_code
        self.data = data or {}


class AuthenticationError(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication failed.'
    default_code = 'authentication_failed'


class AuthorizationError(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'permission_denied'


class ValidationError(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid input.'
    default_code = 'validation_error'


class AccountLockedError(BaseAPIException):
    status_code = status.HTTP_423_LOCKED
    default_detail = 'Account is temporarily locked due to too many failed attempts.'
    default_code = 'account_locked'


class AccountInactiveError(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Account is inactive.'
    default_code = 'account_inactive'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        payload = {
            'error': {
                'code': getattr(exc, 'default_code', 'error'),
                'message': response.data,
                'status': response.status_code,
            }
        }
        if hasattr(exc, 'data') and exc.data:
            payload['error']['data'] = exc.data
        response.data = payload
        return response

    if isinstance(exc, Exception):
        import logging
        logger = logging.getLogger(__name__)
        logger.exception('Unhandled exception: %s', exc)
        return JsonResponse(
            {
                'error': {
                    'code': 'server_error',
                    'message': 'An internal server error occurred.',
                    'status': 500,
                }
            },
            status=500,
        )
    return response
