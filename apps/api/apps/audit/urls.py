from rest_framework.routers import SimpleRouter
from django.urls import path, include

from .views import AuditEventViewSet

router = SimpleRouter()
router.register(r'', AuditEventViewSet, basename='audit-event')

urlpatterns = [
    path('', include(router.urls)),
]
