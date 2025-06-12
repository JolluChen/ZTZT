from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.http import JsonResponse

# Swagger文档配置
schema_view = get_schema_view(
   openapi.Info(
      title="最小化AI平台 API",
      default_version='v1',
      description="AI平台后端API文档",
      contact=openapi.Contact(email="admin@example.com"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

def api_root(request):
    """API根端点"""
    return JsonResponse({
        'message': '欢迎使用最小化AI平台API',
        'version': 'v1',
        'endpoints': {
            'auth': '/api/auth/',
            'algorithm': '/api/algorithm/',
            'data': '/api/data/',
            'model': '/api/model/',
            'service': '/api/service/',
            'swagger': '/swagger/',
            'redoc': '/redoc/',
            'admin': '/admin/'
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root-duplicate'),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/data/', include('apps.data_platform.urls')),
    path('api/algorithm/', include('apps.algorithm_platform.urls')),
    path('api/model/', include('apps.model_platform.urls')),
    path('api/service/', include('apps.service_platform.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# 在开发环境下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
