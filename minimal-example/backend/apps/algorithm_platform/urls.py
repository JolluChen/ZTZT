from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.AlgorithmProjectViewSet)
router.register(r'experiments', views.ExperimentViewSet)
router.register(r'runs', views.ExperimentRunViewSet)
router.register(r'algorithms', views.AlgorithmViewSet)

app_name = 'algorithm_platform'

urlpatterns = [
    path('', include(router.urls)),
]
