from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'data-sources', views.DataSourceViewSet, basename='datasource')
router.register(r'datasets', views.DatasetViewSet, basename='dataset')
router.register(r'processing-tasks', views.DataProcessingTaskViewSet, basename='processing-task')

app_name = 'data_platform'

urlpatterns = [
    path('', include(router.urls)),
]
