from rest_framework import serializers
from .models import MLModel, ModelVersion, ModelEndpoint, ModelPrediction, ModelRegistry


class MLModelSerializer(serializers.ModelSerializer):
    """机器学习模型序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    versions_count = serializers.SerializerMethodField()
    latest_version = serializers.SerializerMethodField()
    active_endpoints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MLModel
        fields = [
            'id', 'name', 'description', 'model_type', 'framework',
            'source_experiment', 'status', 'created_by_name', 'organization_name',
            'versions_count', 'latest_version', 'active_endpoints_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_versions_count(self, obj):
        return obj.versions.count()
    
    def get_latest_version(self, obj):
        latest = obj.versions.filter(is_latest=True).first()
        return latest.version if latest else None
    
    def get_active_endpoints_count(self, obj):
        return ModelEndpoint.objects.filter(
            model_version__model=obj,
            status='active'
        ).count()


class ModelVersionSerializer(serializers.ModelSerializer):
    """模型版本序列化器"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    endpoints_count = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = ModelVersion
        fields = [
            'id', 'model', 'version', 'description', 'model_file',
            'model_size', 'model_format', 'metrics', 'hyperparameters',
            'training_config', 'is_latest', 'is_active', 'model_name',
            'endpoints_count', 'file_size_mb', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'model_size']
    
    def get_endpoints_count(self, obj):
        return obj.endpoints.count()
    
    def get_file_size_mb(self, obj):
        if obj.model_size:
            return round(obj.model_size / (1024 * 1024), 2)
        return None


class ModelEndpointSerializer(serializers.ModelSerializer):
    """模型端点序列化器"""
    model_name = serializers.CharField(source='model_version.model.name', read_only=True)
    model_version_name = serializers.CharField(source='model_version.version', read_only=True)
    predictions_count = serializers.SerializerMethodField()
    health_status = serializers.SerializerMethodField()
    
    class Meta:
        model = ModelEndpoint
        fields = [
            'id', 'model_version', 'name', 'description', 'endpoint_url',
            'api_key', 'deployment_config', 'resource_requirements', 'status',
            'health_check_url', 'last_health_check', 'model_name',
            'model_version_name', 'predictions_count', 'health_status',
            'created_at', 'updated_at', 'deployed_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_predictions_count(self, obj):
        return obj.predictions.count()
    
    def get_health_status(self, obj):
        if obj.last_health_check:
            from datetime import datetime, timedelta
            if datetime.now() - obj.last_health_check.replace(tzinfo=None) < timedelta(minutes=5):
                return 'healthy'
            else:
                return 'unhealthy'
        return 'unknown'


class ModelPredictionSerializer(serializers.ModelSerializer):
    """模型预测记录序列化器"""
    endpoint_name = serializers.CharField(source='endpoint.name', read_only=True)
    model_name = serializers.CharField(source='endpoint.model_version.model.name', read_only=True)
    
    class Meta:
        model = ModelPrediction
        fields = [
            'id', 'endpoint', 'request_id', 'input_data', 'output_data',
            'prediction_result', 'confidence_score', 'latency_ms',
            'processing_time_ms', 'user_agent', 'ip_address', 'status',
            'error_message', 'endpoint_name', 'model_name', 'created_at'
        ]
        read_only_fields = ['created_at', 'request_id']


class ModelRegistrySerializer(serializers.ModelSerializer):
    """模型注册表序列化器"""
    model_name = serializers.CharField(source='model.name', read_only=True)
    model_type = serializers.CharField(source='model.model_type', read_only=True)
    
    class Meta:
        model = ModelRegistry
        fields = [
            'id', 'model', 'registry_name', 'registry_tags', 'model_schema',
            'input_schema', 'output_schema', 'validation_dataset',
            'validation_metrics', 'is_public', 'is_approved', 'approval_notes',
            'model_name', 'model_type', 'registered_at', 'approved_at'
        ]
        read_only_fields = ['registered_at', 'approved_at']


class ModelCreateSerializer(serializers.ModelSerializer):
    """模型创建序列化器"""
    
    class Meta:
        model = MLModel
        fields = [
            'name', 'description', 'model_type', 'framework', 'source_experiment'
        ]


class ModelVersionCreateSerializer(serializers.ModelSerializer):
    """模型版本创建序列化器"""
    
    class Meta:
        model = ModelVersion
        fields = [
            'model', 'version', 'description', 'model_file', 'model_format',
            'metrics', 'hyperparameters', 'training_config'
        ]


class ModelPredictionCreateSerializer(serializers.ModelSerializer):
    """模型预测创建序列化器"""
    
    class Meta:
        model = ModelPrediction
        fields = [
            'endpoint', 'input_data'
        ]