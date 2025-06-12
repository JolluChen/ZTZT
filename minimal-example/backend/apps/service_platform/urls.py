"""
服务中台URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ServiceCategoryViewSet, ApplicationViewSet, ApplicationVersionViewSet,
    ServiceEndpointViewSet, ServiceMonitoringViewSet, 
    ServiceTemplateViewSet, ServiceAlertViewSet
)

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'versions', ApplicationVersionViewSet)
router.register(r'endpoints', ServiceEndpointViewSet)
router.register(r'monitoring', ServiceMonitoringViewSet)
router.register(r'templates', ServiceTemplateViewSet)
router.register(r'alerts', ServiceAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
