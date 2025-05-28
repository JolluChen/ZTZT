from rest_framework import serializers
from .models import AlgorithmProject, Experiment, ExperimentRun, Algorithm


class AlgorithmProjectSerializer(serializers.ModelSerializer):
    """算法项目序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    experiments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlgorithmProject
        fields = [
            'id', 'name', 'description', 'framework', 'environment_config',
            'git_repository', 'is_active', 'created_by_name', 'organization_name',
            'experiments_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_experiments_count(self, obj):
        return obj.experiments.count()


class ExperimentSerializer(serializers.ModelSerializer):
    """实验序列化器"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    runs_count = serializers.SerializerMethodField()
    latest_run_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Experiment
        fields = [
            'id', 'project', 'name', 'description', 'algorithm_type',
            'dataset', 'hyperparameters', 'status', 'project_name',
            'created_by_name', 'dataset_name', 'runs_count', 'latest_run_status',
            'created_at', 'updated_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_runs_count(self, obj):
        return obj.runs.count()
    
    def get_latest_run_status(self, obj):
        latest_run = obj.runs.first()
        return latest_run.status if latest_run else None


class ExperimentRunSerializer(serializers.ModelSerializer):
    """实验运行记录序列化器"""
    experiment_name = serializers.CharField(source='experiment.name', read_only=True)
    project_name = serializers.CharField(source='experiment.project.name', read_only=True)
    duration_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = ExperimentRun
        fields = [
            'id', 'experiment', 'run_id', 'version', 'parameters',
            'metrics', 'artifacts', 'status', 'experiment_name', 'project_name',
            'started_at', 'ended_at', 'duration', 'duration_seconds',
            'resource_usage', 'logs', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'run_id']
    
    def get_duration_seconds(self, obj):
        if obj.duration:
            return obj.duration.total_seconds()
        return None


class AlgorithmSerializer(serializers.ModelSerializer):
    """算法模板序列化器"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Algorithm
        fields = [
            'id', 'name', 'description', 'category', 'framework',
            'code_template', 'default_parameters', 'author', 'version',
            'documentation', 'is_builtin', 'is_active', 'organization_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ExperimentCreateSerializer(serializers.ModelSerializer):
    """实验创建序列化器"""
    
    class Meta:
        model = Experiment
        fields = [
            'project', 'name', 'description', 'algorithm_type',
            'dataset', 'hyperparameters'
        ]
