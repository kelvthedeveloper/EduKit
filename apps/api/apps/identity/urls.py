from rest_framework.routers import DefaultRouter, SimpleRouter
from django.urls import path, include

from .views import (
    LoginView, LogoutView, MeView, RefreshSessionView,
    PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView,
    SessionViewSet,
    EmailVerifyRequestView, EmailVerifyConfirmView,
    PhoneVerifyRequestView, PhoneVerifyConfirmView,
)

router = SimpleRouter()
router.register(r'sessions', SessionViewSet, basename='auth-session')

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('session/refresh/', RefreshSessionView.as_view(), name='auth-session-refresh'),
    path('password/change/', PasswordChangeView.as_view(), name='auth-password-change'),
    path('password/reset/request/', PasswordResetRequestView.as_view(),
         name='auth-password-reset-request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(),
         name='auth-password-reset-confirm'),
    path('verify/email/request/', EmailVerifyRequestView.as_view(),
         name='auth-verify-email-request'),
    path('verify/email/confirm/', EmailVerifyConfirmView.as_view(),
         name='auth-verify-email-confirm'),
    path('verify/phone/request/', PhoneVerifyRequestView.as_view(),
         name='auth-verify-phone-request'),
    path('verify/phone/confirm/', PhoneVerifyConfirmView.as_view(),
         name='auth-verify-phone-confirm'),
    path('', include(router.urls)),
]
