"""
服务中台序列化器
"""
from rest_framework import serializers
from .models import (
    ServiceCategory, Application, ApplicationVersion, 
    ServiceEndpoint, ServiceMonitoring, ServiceTemplate, ServiceAlert
)


class ServiceCategorySerializer(serializers.ModelSerializer):
    """服务分类序列化器"""
    
    class Meta:
        model = ServiceCategory
        fields = '__all__'


class ApplicationSerializer(serializers.ModelSerializer):
    """AI应用序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    latest_version = serializers.SerializerMethodField()
    deployment_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ('created_by', 'view_count', 'deployment_count')
    
    def get_latest_version(self, obj):
        """获取最新版本"""
        latest = obj.versions.first()
        if latest:
            return latest.version
        return None
    
    def get_deployment_status(self, obj):
        """获取部署状态"""
        latest_version = obj.versions.first()
        if latest_version:
            endpoints = latest_version.endpoints.all()
            if not endpoints:
                return 'not_deployed'
            
            statuses = [ep.status for ep in endpoints]
            if all(status == 'running' for status in statuses):
                return 'running'
            elif any(status in ['error', 'stopped'] for status in statuses):
                return 'error'
            else:
                return 'starting'
        return 'not_deployed'


class ApplicationVersionSerializer(serializers.ModelSerializer):
    """应用版本序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    application_name = serializers.CharField(source='application.name', read_only=True)
    endpoints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ApplicationVersion
        fields = '__all__'
        read_only_fields = ('created_by', 'build_log')
    
    def get_endpoints_count(self, obj):
        """获取端点数量"""
        return obj.endpoints.count()


class ServiceEndpointSerializer(serializers.ModelSerializer):
    """服务端点序列化器"""
    application_name = serializers.CharField(source='application_version.application.name', read_only=True)
    version = serializers.CharField(source='application_version.version', read_only=True)
    url = serializers.ReadOnlyField()
    health_status = serializers.SerializerMethodField()
    latest_metrics = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceEndpoint
        fields = '__all__'
        read_only_fields = ('last_health_check', 'is_healthy')
    
    def get_health_status(self, obj):
        """获取健康状态"""
        if obj.status != 'running':
            return obj.status
        return 'healthy' if obj.is_healthy else 'unhealthy'
    
    def get_latest_metrics(self, obj):
        """获取最新监控指标"""
        latest = obj.monitoring_data.first()
        if latest:
            return {
                'cpu_usage': latest.cpu_usage,
                'memory_usage': latest.memory_usage,
                'response_time': latest.response_time,
                'request_count': latest.request_count,
                'error_count': latest.error_count,
                'timestamp': latest.timestamp
            }
        return None


class ServiceMonitoringSerializer(serializers.ModelSerializer):
    """服务监控序列化器"""
    endpoint_name = serializers.CharField(source='endpoint.name', read_only=True)
    
    class Meta:
        model = ServiceMonitoring
        fields = '__all__'
        read_only_fields = ('timestamp',)


class ServiceTemplateSerializer(serializers.ModelSerializer):
    """服务模板序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ServiceTemplate
        fields = '__all__'
        read_only_fields = ('created_by', 'usage_count')


class ServiceAlertSerializer(serializers.ModelSerializer):
    """服务告警序列化器"""
    endpoint_name = serializers.CharField(source='endpoint.name', read_only=True)
    application_name = serializers.CharField(source='endpoint.application_version.application.name', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceAlert
        fields = '__all__'
        read_only_fields = ('triggered_at', 'resolved_at', 'acknowledged_at', 'acknowledged_by')
    
    def get_duration(self, obj):
        """获取告警持续时间（秒）"""
        end_time = obj.resolved_at or obj.acknowledged_at
        if end_time:
            return int((end_time - obj.triggered_at).total_seconds())
        return None


# 详细序列化器（包含关联数据）
class ApplicationDetailSerializer(ApplicationSerializer):
    """应用详细信息序列化器"""
    versions = ApplicationVersionSerializer(many=True, read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    
    class Meta(ApplicationSerializer.Meta):
        pass


class ApplicationVersionDetailSerializer(ApplicationVersionSerializer):
    """应用版本详细信息序列化器"""
    endpoints = ServiceEndpointSerializer(many=True, read_only=True)
    application = ApplicationSerializer(read_only=True)
    
    class Meta(ApplicationVersionSerializer.Meta):
        pass


class ServiceEndpointDetailSerializer(ServiceEndpointSerializer):
    """服务端点详细信息序列化器"""
    monitoring_data = ServiceMonitoringSerializer(many=True, read_only=True, source='monitoring_data')
    alerts = ServiceAlertSerializer(many=True, read_only=True)
    application_version = ApplicationVersionSerializer(read_only=True)
    
    class Meta(ServiceEndpointSerializer.Meta):
        pass
