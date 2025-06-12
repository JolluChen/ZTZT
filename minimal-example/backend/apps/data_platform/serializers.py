from rest_framework import serializers
from .models import DataSource, Dataset, DataProcessingTask


class DataSourceSerializer(serializers.ModelSerializer):
    """数据源序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = DataSource
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class DatasetSerializer(serializers.ModelSerializer):
    """数据集序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Dataset
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at', 'size_bytes')
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class DatasetUploadSerializer(serializers.ModelSerializer):
    """数据集上传序列化器"""
    
    class Meta:
        model = Dataset
        fields = ('name', 'description', 'file', 'format', 'tags', 'is_public')
    
    def create(self, validated_data):
        # 自动设置文件大小
        if validated_data.get('file'):
            validated_data['size_bytes'] = validated_data['file'].size
        return super().create(validated_data)


class DataProcessingTaskSerializer(serializers.ModelSerializer):
    """数据处理任务序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    source_dataset_name = serializers.CharField(source='source_dataset.name', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = DataProcessingTask
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'started_at', 'completed_at', 'status', 'status_message', 'result_data')
    
    def get_duration(self, obj):
        if obj.started_at and obj.completed_at:
            duration = obj.completed_at - obj.started_at
            return duration.total_seconds()
        return None


class DataProcessingTaskCreateSerializer(serializers.ModelSerializer):
    """数据处理任务创建序列化器"""
    
    class Meta:
        model = DataProcessingTask
        fields = ('name', 'description', 'task_type', 'source_dataset', 'configuration')
