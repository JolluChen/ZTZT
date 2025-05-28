from django.contrib import admin
from .models import AlgorithmProject, Experiment, ExperimentRun, Algorithm


@admin.register(AlgorithmProject)
class AlgorithmProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'framework', 'organization', 'created_by', 'is_active', 'created_at']
    list_filter = ['framework', 'is_active', 'organization', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'algorithm_type', 'status', 'created_by', 'created_at']
    list_filter = ['algorithm_type', 'status', 'project', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']


@admin.register(ExperimentRun)
class ExperimentRunAdmin(admin.ModelAdmin):
    list_display = ['run_id', 'experiment', 'version', 'status', 'started_at', 'ended_at']
    list_filter = ['status', 'experiment', 'started_at']
    search_fields = ['run_id']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'ended_at', 'duration']


@admin.register(Algorithm)
class AlgorithmAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'framework', 'version', 'is_builtin', 'is_active', 'created_at']
    list_filter = ['category', 'framework', 'is_builtin', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'author']
    readonly_fields = ['created_at', 'updated_at']
