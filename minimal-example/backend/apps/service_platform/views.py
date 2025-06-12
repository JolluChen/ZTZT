"""
服务中台视图
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from datetime import timedelta
import json
import yaml

from .models import (
    ServiceCategory, Application, ApplicationVersion, 
    ServiceEndpoint, ServiceMonitoring, ServiceTemplate, ServiceAlert
)
from .serializers import (
    ServiceCategorySerializer, ApplicationSerializer, ApplicationDetailSerializer,
    ApplicationVersionSerializer, ApplicationVersionDetailSerializer,
    ServiceEndpointSerializer, ServiceEndpointDetailSerializer,
    ServiceMonitoringSerializer, ServiceTemplateSerializer, ServiceAlertSerializer
)


class ServiceCategoryViewSet(viewsets.ModelViewSet):
    """服务分类管理"""
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        """获取分类下的应用"""
        category = self.get_object()
        applications = Application.objects.filter(category=category)
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data)


class ApplicationViewSet(viewsets.ModelViewSet):
    """AI应用管理"""
    queryset = Application.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ApplicationDetailSerializer
        return ApplicationSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        queryset = Application.objects.all()
        
        # 过滤条件
        category = self.request.query_params.get('category')
        app_type = self.request.query_params.get('type')
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category_id=category)
        if app_type:
            queryset = queryset.filter(app_type=app_type)
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(display_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """克隆应用"""
        original = self.get_object()
        
        # 创建新应用
        new_app = Application.objects.create(
            name=f"{original.name}_copy",
            display_name=f"{original.display_name} (副本)",
            description=original.description,
            category=original.category,
            app_type=original.app_type,
            components=original.components.copy(),
            dependencies=original.dependencies.copy(),
            created_by=request.user,
            status='draft'
        )
        
        serializer = ApplicationSerializer(new_app)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """更改应用状态"""
        app = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Application.STATUS_CHOICES):
            return Response(
                {'error': '无效的状态值'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        app.status = new_status
        app.save()
        
        serializer = ApplicationSerializer(app)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取应用统计信息"""
        app = self.get_object()
        
        # 统计数据
        versions_count = app.versions.count()
        active_endpoints = ServiceEndpoint.objects.filter(
            application_version__application=app,
            status='running'
        ).count()
        
        # 最近7天的监控数据
        week_ago = timezone.now() - timedelta(days=7)
        recent_monitoring = ServiceMonitoring.objects.filter(
            endpoint__application_version__application=app,
            timestamp__gte=week_ago
        )
        
        avg_response_time = recent_monitoring.aggregate(
            avg_response=Avg('response_time')
        )['avg_response'] or 0
        
        total_requests = recent_monitoring.aggregate(
            total=Count('request_count')
        )['total'] or 0
        
        # 告警统计
        active_alerts = ServiceAlert.objects.filter(
            endpoint__application_version__application=app,
            status='active'
        ).count()
        
        return Response({
            'versions_count': versions_count,
            'active_endpoints': active_endpoints,
            'avg_response_time': round(avg_response_time, 2),
            'total_requests': total_requests,
            'active_alerts': active_alerts,
            'view_count': app.view_count,
            'deployment_count': app.deployment_count
        })


class ApplicationVersionViewSet(viewsets.ModelViewSet):
    """应用版本管理"""
    queryset = ApplicationVersion.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ApplicationVersionDetailSerializer
        return ApplicationVersionSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        queryset = ApplicationVersion.objects.all()
        
        application = self.request.query_params.get('application')
        if application:
            queryset = queryset.filter(application_id=application)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def build(self, request, pk=None):
        """构建版本"""
        version = self.get_object()
        
        if version.status not in ['building', 'build_failed', 'ready']:
            return Response(
                {'error': '当前状态不允许构建'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 模拟构建过程
        version.status = 'building'
        version.build_log = "开始构建...\n"
        version.save()
        
        # 这里可以触发实际的构建任务
        # 例如：build_version_task.delay(version.id)
        
        return Response({'message': '构建已开始'})
    
    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """部署版本"""
        version = self.get_object()
        
        if version.status != 'ready':
            return Response(
                {'error': '版本未就绪，无法部署'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 部署配置
        replicas = request.data.get('replicas', 1)
        env_vars = request.data.get('env_vars', {})
        
        # 创建服务端点
        endpoint = ServiceEndpoint.objects.create(
            application_version=version,
            name=f"{version.application.name}-{version.version}",
            protocol='http',
            host='cluster.local',
            port=8080,
            replicas=replicas,
            status='starting'
        )
        
        # 更新部署计数
        version.application.deployment_count += 1
        version.application.save()
        
        serializer = ServiceEndpointSerializer(endpoint)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取构建日志"""
        version = self.get_object()
        return Response({'logs': version.build_log})


class ServiceEndpointViewSet(viewsets.ModelViewSet):
    """服务端点管理"""
    queryset = ServiceEndpoint.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ServiceEndpointDetailSerializer
        return ServiceEndpointSerializer
    
    def get_queryset(self):
        queryset = ServiceEndpoint.objects.all()
        
        application = self.request.query_params.get('application')
        status_filter = self.request.query_params.get('status')
        
        if application:
            queryset = queryset.filter(application_version__application_id=application)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动服务"""
        endpoint = self.get_object()
        
        if endpoint.status in ['running', 'starting']:
            return Response({'error': '服务已在运行或启动中'})
        
        endpoint.status = 'starting'
        endpoint.save()
        
        # 这里可以触发实际的启动任务
        
        return Response({'message': '服务启动中'})
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止服务"""
        endpoint = self.get_object()
        
        if endpoint.status in ['stopped', 'stopping']:
            return Response({'error': '服务已停止或停止中'})
        
        endpoint.status = 'stopping'
        endpoint.save()
        
        # 这里可以触发实际的停止任务
        
        return Response({'message': '服务停止中'})
    
    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """重启服务"""
        endpoint = self.get_object()
        
        endpoint.status = 'starting'
        endpoint.save()
        
        return Response({'message': '服务重启中'})
    
    @action(detail=True, methods=['post'])
    def scale(self, request, pk=None):
        """扩缩容"""
        endpoint = self.get_object()
        replicas = request.data.get('replicas')
        
        if not replicas or not isinstance(replicas, int) or replicas < 1 or replicas > 10:
            return Response(
                {'error': '副本数必须是1-10的整数'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        endpoint.replicas = replicas
        endpoint.save()
        
        return Response({'message': f'服务已扩缩容至{replicas}个副本'})
    
    @action(detail=True, methods=['get'])
    def health(self, request, pk=None):
        """健康检查"""
        endpoint = self.get_object()
        
        # 这里可以实现实际的健康检查逻辑
        is_healthy = endpoint.status == 'running'
        
        endpoint.is_healthy = is_healthy
        endpoint.last_health_check = timezone.now()
        endpoint.save()
        
        return Response({
            'is_healthy': is_healthy,
            'status': endpoint.status,
            'last_check': endpoint.last_health_check
        })
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """获取监控指标"""
        endpoint = self.get_object()
        
        # 时间范围
        hours = int(request.query_params.get('hours', 24))
        start_time = timezone.now() - timedelta(hours=hours)
        
        monitoring_data = endpoint.monitoring_data.filter(
            timestamp__gte=start_time
        ).order_by('timestamp')
        
        serializer = ServiceMonitoringSerializer(monitoring_data, many=True)
        return Response(serializer.data)


class ServiceMonitoringViewSet(viewsets.ReadOnlyModelViewSet):
    """服务监控数据"""
    queryset = ServiceMonitoring.objects.all()
    serializer_class = ServiceMonitoringSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ServiceMonitoring.objects.all()
        
        endpoint = self.request.query_params.get('endpoint')
        hours = self.request.query_params.get('hours', 24)
        
        if endpoint:
            queryset = queryset.filter(endpoint_id=endpoint)
        
        # 时间过滤
        start_time = timezone.now() - timedelta(hours=int(hours))
        queryset = queryset.filter(timestamp__gte=start_time)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """监控数据汇总"""
        # 获取所有活跃端点的最新监控数据
        latest_data = {}
        
        for endpoint in ServiceEndpoint.objects.filter(status='running'):
            latest = endpoint.monitoring_data.first()
            if latest:
                latest_data[str(endpoint.id)] = {
                    'endpoint_name': endpoint.name,
                    'cpu_usage': latest.cpu_usage,
                    'memory_usage': latest.memory_usage,
                    'response_time': latest.response_time,
                    'request_count': latest.request_count,
                    'error_count': latest.error_count,
                    'timestamp': latest.timestamp
                }
        
        return Response(latest_data)


class ServiceTemplateViewSet(viewsets.ModelViewSet):
    """服务模板管理"""
    queryset = ServiceTemplate.objects.all()
    serializer_class = ServiceTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        queryset = ServiceTemplate.objects.all()
        
        template_type = self.request.query_params.get('type')
        is_public = self.request.query_params.get('public')
        
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        
        return queryset.order_by('-usage_count', 'name')
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """使用模板创建应用"""
        template = self.get_object()
        
        # 获取应用信息
        app_name = request.data.get('name')
        app_display_name = request.data.get('display_name', app_name)
        app_description = request.data.get('description', '')
        custom_config = request.data.get('config', {})
        
        if not app_name:
            return Response(
                {'error': '应用名称不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 合并配置
        final_config = template.default_config.copy()
        final_config.update(custom_config)
        
        # 创建应用
        application = Application.objects.create(
            name=app_name,
            display_name=app_display_name,
            description=app_description,
            app_type='web_service',  # 从模板类型映射
            components=final_config,
            created_by=request.user,
            status='draft'
        )
        
        # 增加使用计数
        template.usage_count += 1
        template.save()
        
        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ServiceAlertViewSet(viewsets.ModelViewSet):
    """服务告警管理"""
    queryset = ServiceAlert.objects.all()
    serializer_class = ServiceAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ServiceAlert.objects.all()
        
        level = self.request.query_params.get('level')
        status_filter = self.request.query_params.get('status')
        endpoint = self.request.query_params.get('endpoint')
        
        if level:
            queryset = queryset.filter(level=level)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if endpoint:
            queryset = queryset.filter(endpoint_id=endpoint)
        
        return queryset.order_by('-triggered_at')
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """确认告警"""
        alert = self.get_object()
        
        if alert.status != 'active':
            return Response({'error': '只能确认活跃状态的告警'})
        
        alert.status = 'acknowledged'
        alert.acknowledged_at = timezone.now()
        alert.acknowledged_by = request.user
        alert.save()
        
        return Response({'message': '告警已确认'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决告警"""
        alert = self.get_object()
        
        if alert.status in ['resolved', 'ignored']:
            return Response({'error': '告警已解决或忽略'})
        
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        
        return Response({'message': '告警已解决'})
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """告警仪表盘"""
        # 按级别统计
        level_stats = {}
        for level, _ in ServiceAlert.LEVEL_CHOICES:
            level_stats[level] = ServiceAlert.objects.filter(
                level=level, 
                status='active'
            ).count()
        
        # 最近24小时趋势
        day_ago = timezone.now() - timedelta(days=1)
        recent_alerts = ServiceAlert.objects.filter(
            triggered_at__gte=day_ago
        ).count()
        
        # Top问题端点
        problem_endpoints = ServiceAlert.objects.filter(
            status='active'
        ).values(
            'endpoint__name'
        ).annotate(
            alert_count=Count('id')
        ).order_by('-alert_count')[:5]
        
        return Response({
            'level_stats': level_stats,
            'recent_alerts_24h': recent_alerts,
            'problem_endpoints': list(problem_endpoints)
        })
