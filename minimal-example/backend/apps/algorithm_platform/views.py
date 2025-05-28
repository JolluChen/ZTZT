import uuid
from datetime import datetime
from django.utils import timezone
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import AlgorithmProject, Experiment, ExperimentRun, Algorithm
from .serializers import (
    AlgorithmProjectSerializer, ExperimentSerializer, ExperimentRunSerializer,
    AlgorithmSerializer, ExperimentCreateSerializer
)


class AlgorithmProjectViewSet(viewsets.ModelViewSet):
    """算法项目ViewSet"""
    queryset = AlgorithmProject.objects.all()
    serializer_class = AlgorithmProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'creator']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return AlgorithmProject.objects.all()
        return AlgorithmProject.objects.filter(creator=user)

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """克隆算法项目"""
        project = self.get_object()
        new_project = AlgorithmProject.objects.create(
            name=f"{project.name}_copy_{uuid.uuid4().hex[:8]}",
            description=f"克隆自: {project.name}",
            creator=request.user,
            config=project.config
        )
        serializer = self.get_serializer(new_project)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ExperimentViewSet(viewsets.ModelViewSet):
    """实验ViewSet"""
    queryset = Experiment.objects.all()
    serializer_class = ExperimentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'project']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return Experiment.objects.all()
        return Experiment.objects.filter(project__creator=user)

    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'create':
            return ExperimentCreateSerializer
        return ExperimentSerializer

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动实验"""
        experiment = self.get_object()
        if experiment.status == 'running':
            return Response(
                {'error': '实验已在运行中'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建实验运行记录
        run = ExperimentRun.objects.create(
            experiment=experiment,
            status='running',
            started_at=timezone.now(),
            config=experiment.config
        )
        
        experiment.status = 'running'
        experiment.save()
        
        return Response({
            'message': '实验启动成功',
            'run_id': run.id
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止实验"""
        experiment = self.get_object()
        if experiment.status != 'running':
            return Response(
                {'error': '实验未在运行中'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 更新最新的运行记录
        latest_run = experiment.runs.filter(status='running').first()
        if latest_run:
            latest_run.status = 'stopped'
            latest_run.finished_at = timezone.now()
            latest_run.save()
        
        experiment.status = 'stopped'
        experiment.save()
        
        return Response({
            'message': '实验停止成功'
        }, status=status.HTTP_200_OK)


class ExperimentRunViewSet(viewsets.ModelViewSet):
    """实验运行ViewSet"""
    queryset = ExperimentRun.objects.all()
    serializer_class = ExperimentRunSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'experiment']
    ordering_fields = ['started_at', 'finished_at']
    ordering = ['-started_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return ExperimentRun.objects.all()
        return ExperimentRun.objects.filter(experiment__project__creator=user)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取实验运行日志"""
        run = self.get_object()
        return Response({
            'logs': run.logs or '暂无日志',
            'status': run.status
        })

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """获取实验运行指标"""
        run = self.get_object()
        return Response({
            'metrics': run.metrics or {},
            'status': run.status
        })


class AlgorithmViewSet(viewsets.ModelViewSet):
    """算法ViewSet"""
    queryset = Algorithm.objects.all()
    serializer_class = AlgorithmSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_public']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return Algorithm.objects.all()
        # 用户可以看到公开的算法和自己创建的算法
        return Algorithm.objects.filter(
            models.Q(is_public=True) | models.Q(creator=user)
        )

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """测试算法"""
        algorithm = self.get_object()
        test_data = request.data.get('test_data', {})
        
        # 这里应该实现具体的算法测试逻辑
        # 目前返回模拟结果
        result = {
            'algorithm_id': algorithm.id,
            'test_data': test_data,
            'result': '测试结果（模拟）',
            'timestamp': timezone.now().isoformat()
        }
        
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """获取算法版本历史"""
        algorithm = self.get_object()
        # 这里应该实现版本管理逻辑
        # 目前返回模拟数据
        versions = [
            {
                'version': '1.0.0',
                'created_at': algorithm.created_at.isoformat(),
                'description': '初始版本'
            }
        ]
        return Response(versions, status=status.HTTP_200_OK)
