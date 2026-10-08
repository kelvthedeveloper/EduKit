from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def api_v1_root(request):
    return JsonResponse({
        'version': 'v1',
        'message': 'EduKit API v1',
        'endpoints': {
            'auth': '/api/v1/auth/',
            'permissions': '/api/v1/permissions/',
            'audit': '/api/v1/audit/',
        },
    })


health_urls = [
    path('healthz/', lambda r: JsonResponse({'status': 'ok'})),
    path('readyz/', lambda r: JsonResponse({'status': 'ready'})),
]

api_v1_urls = [
    path('', api_v1_root, name='api-v1-root'),
    path('auth/', include('apps.identity.urls')),
    path('permissions/', include('apps.permissions.urls')),
    path('audit/', include('apps.audit.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_urls)),
    path('', include(health_urls)),
]
