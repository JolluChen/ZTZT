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
from .dify_views import (
    DifyApplicationViewSet, DifyConversationViewSet, DifyDatasetViewSet
)

router = DefaultRouter()
router.register(r'categories', ServiceCategoryViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'versions', ApplicationVersionViewSet)
router.register(r'endpoints', ServiceEndpointViewSet)
router.register(r'monitoring', ServiceMonitoringViewSet)
router.register(r'templates', ServiceTemplateViewSet)
router.register(r'alerts', ServiceAlertViewSet)

# Dify 集成路由
router.register(r'dify/applications', DifyApplicationViewSet, basename='dify-applications')
router.register(r'dify/conversations', DifyConversationViewSet, basename='dify-conversations')
router.register(r'dify/datasets', DifyDatasetViewSet, basename='dify-datasets')

urlpatterns = [
    path('', include(router.urls)),
]
