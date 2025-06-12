"""
服务中台管理后台配置
"""
from django.contrib import admin
from .models import (
    ServiceCategory, Application, ApplicationVersion, 
    ServiceEndpoint, ServiceMonitoring, ServiceTemplate, ServiceAlert
)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'app_type', 'status', 'version', 'created_by', 'created_at')
    list_filter = ('app_type', 'status', 'category', 'created_at')
    search_fields = ('name', 'display_name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at', 'view_count', 'deployment_count')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'name', 'display_name', 'description', 'category')
        }),
        ('应用配置', {
            'fields': ('app_type', 'status', 'version', 'components', 'dependencies')
        }),
        ('统计信息', {
            'fields': ('view_count', 'deployment_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ApplicationVersion)
class ApplicationVersionAdmin(admin.ModelAdmin):
    list_display = ('application', 'version', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at', 'application__app_type')
    search_fields = ('application__name', 'version', 'description')
    readonly_fields = ('id', 'created_at', 'build_log')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'application', 'version', 'description')
        }),
        ('版本配置', {
            'fields': ('config', 'dockerfile', 'requirements')
        }),
        ('部署信息', {
            'fields': ('image_url', 'manifest', 'status')
        }),
        ('构建信息', {
            'fields': ('build_log', 'created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ServiceEndpoint)
class ServiceEndpointAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_application_name', 'protocol', 'host', 'port', 'status', 'replicas', 'is_healthy')
    list_filter = ('protocol', 'status', 'is_healthy', 'created_at')
    search_fields = ('name', 'host', 'application_version__application__name')
    readonly_fields = ('id', 'url', 'last_health_check', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def get_application_name(self, obj):
        return obj.application_version.application.name
    get_application_name.short_description = '应用名称'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'application_version', 'name', 'url')
        }),
        ('网络配置', {
            'fields': ('protocol', 'host', 'port', 'path')
        }),
        ('运行状态', {
            'fields': ('status', 'replicas', 'health_check_path', 'is_healthy', 'last_health_check')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ServiceMonitoring)
class ServiceMonitoringAdmin(admin.ModelAdmin):
    list_display = ('get_endpoint_name', 'cpu_usage', 'memory_usage', 'response_time', 'request_count', 'error_count', 'timestamp')
    list_filter = ('timestamp', 'endpoint__status')
    search_fields = ('endpoint__name', 'endpoint__application_version__application__name')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def get_endpoint_name(self, obj):
        return obj.endpoint.name
    get_endpoint_name.short_description = '端点名称'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('endpoint', 'timestamp')
        }),
        ('性能指标', {
            'fields': ('cpu_usage', 'memory_usage', 'response_time', 'request_count', 'error_count')
        }),
        ('网络指标', {
            'fields': ('network_in', 'network_out')
        }),
        ('自定义指标', {
            'fields': ('custom_metrics',),
            'classes': ('collapse',)
        })
    )


@admin.register(ServiceTemplate)
class ServiceTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'usage_count', 'is_public', 'created_by', 'created_at')
    list_filter = ('template_type', 'is_public', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('usage_count', 'created_at', 'updated_at')
    ordering = ('-usage_count', 'name')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'template_type', 'is_public')
        }),
        ('模板配置', {
            'fields': ('config_schema', 'default_config', 'dockerfile_template', 'manifest_template')
        }),
        ('统计信息', {
            'fields': ('usage_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ServiceAlert)
class ServiceAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_endpoint_name', 'level', 'status', 'triggered_at', 'acknowledged_by')
    list_filter = ('level', 'status', 'triggered_at')
    search_fields = ('title', 'message', 'endpoint__name')
    readonly_fields = ('triggered_at', 'resolved_at', 'acknowledged_at')
    ordering = ('-triggered_at',)
    
    def get_endpoint_name(self, obj):
        return obj.endpoint.name
    get_endpoint_name.short_description = '端点名称'
    
    fieldsets = (
        ('告警信息', {
            'fields': ('endpoint', 'title', 'message', 'level', 'status')
        }),
        ('规则配置', {
            'fields': ('rule_name', 'condition')
        }),
        ('时间信息', {
            'fields': ('triggered_at', 'resolved_at', 'acknowledged_at', 'acknowledged_by'),
            'classes': ('collapse',)
        })
    )
