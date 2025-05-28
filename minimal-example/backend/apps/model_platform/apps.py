from django.apps import AppConfig


class ModelPlatformConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.model_platform'
    verbose_name = '模型平台'