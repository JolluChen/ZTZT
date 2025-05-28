from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'data-sources', views.DataSourceViewSet)
router.register(r'datasets', views.DatasetViewSet)
router.register(r'processing-tasks', views.DataProcessingTaskViewSet)

app_name = 'data_platform'

urlpatterns = [
    path('', include(router.urls)),
]
