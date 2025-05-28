from django.contrib import admin
from .models import MLModel, ModelVersion, ModelEndpoint, ModelPrediction, ModelRegistry


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'framework', 'status', 'organization', 'created_by', 'created_at']
    list_filter = ['model_type', 'framework', 'status', 'organization', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ['model', 'version', 'model_format', 'model_size', 'is_latest', 'is_active', 'created_at']
    list_filter = ['model_format', 'is_latest', 'is_active', 'model', 'created_at']
    search_fields = ['version', 'description']
    readonly_fields = ['created_at', 'updated_at', 'model_size']


@admin.register(ModelEndpoint)
class ModelEndpointAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_version', 'status', 'endpoint_url', 'created_at', 'deployed_at']
    list_filter = ['status', 'model_version__model', 'created_at']
    search_fields = ['name', 'description', 'endpoint_url']
    readonly_fields = ['created_at', 'updated_at', 'last_health_check']


@admin.register(ModelPrediction)
class ModelPredictionAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'endpoint', 'status', 'confidence_score', 'latency_ms', 'created_at']
    list_filter = ['status', 'endpoint', 'created_at']
    search_fields = ['request_id']
    readonly_fields = ['created_at']


@admin.register(ModelRegistry)
class ModelRegistryAdmin(admin.ModelAdmin):
    list_display = ['registry_name', 'model', 'is_public', 'is_approved', 'registered_at', 'approved_at']
    list_filter = ['is_public', 'is_approved', 'registered_at']
    search_fields = ['registry_name', 'registry_tags']
    readonly_fields = ['registered_at', 'approved_at']
