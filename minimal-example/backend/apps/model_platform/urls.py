from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'models', views.MLModelViewSet)
router.register(r'versions', views.ModelVersionViewSet)
router.register(r'endpoints', views.ModelEndpointViewSet)
router.register(r'predictions', views.ModelPredictionViewSet)
router.register(r'registry', views.ModelRegistryViewSet)

app_name = 'model_platform'

urlpatterns = [
    path('', include(router.urls)),
]
