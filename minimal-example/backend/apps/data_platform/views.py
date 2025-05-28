import pandas as pd
import json
from django.http import HttpResponse
from django.db import models
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser

from .models import DataSource, Dataset, DataProcessingTask
from .serializers import DataSourceSerializer, DatasetSerializer, DataProcessingTaskSerializer


class DataSourceViewSet(viewsets.ModelViewSet):
    """数据源管理ViewSet"""
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['source_type', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return DataSource.objects.all()
        return DataSource.objects.filter(creator=user)

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试数据源连接"""
        data_source = self.get_object()
        
        # 这里应该实现具体的连接测试逻辑
        # 目前返回模拟结果
        try:
            # 模拟连接测试
            connection_result = {
                'status': 'success',
                'message': '连接测试成功',
                'latency': '50ms',
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            data_source.status = 'active'
            data_source.save()
            
            return Response(connection_result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'连接失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def preview_data(self, request, pk=None):
        """预览数据源数据"""
        data_source = self.get_object()
        
        # 这里应该实现具体的数据预览逻辑
        # 目前返回模拟数据
        preview_data = {
            'columns': ['id', 'name', 'value', 'timestamp'],
            'rows': [
                [1, 'sample1', 100.5, '2023-01-01T10:00:00Z'],
                [2, 'sample2', 200.3, '2023-01-01T11:00:00Z'],
                [3, 'sample3', 150.8, '2023-01-01T12:00:00Z']
            ],
            'total_rows': 1000,
            'preview_rows': 3
        }
        
        return Response(preview_data, status=status.HTTP_200_OK)


class DatasetViewSet(viewsets.ModelViewSet):
    """数据集管理ViewSet"""
    queryset = Dataset.objects.all()
    serializer_class = DatasetSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['data_source', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'name', 'size']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return Dataset.objects.all()
        return Dataset.objects.filter(creator=user)

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载数据集"""
        dataset = self.get_object()
        
        if not dataset.file_path:
            return Response({
                'error': '数据集文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 这里应该实现文件下载逻辑
        # 目前返回文件信息
        return Response({
            'download_url': f'/api/datasets/{dataset.id}/file/',
            'filename': dataset.name,
            'size': dataset.size,
            'format': 'csv'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取数据集统计信息"""
        dataset = self.get_object()
        
        # 这里应该实现具体的统计分析逻辑
        # 目前返回模拟统计数据
        stats = {
            'rows': dataset.size if dataset.size else 0,
            'columns': 10,  # 模拟列数
            'missing_values': 5,
            'data_types': {
                'numeric': 6,
                'categorical': 3,
                'datetime': 1
            },
            'memory_usage': '2.5MB'
        }
        
        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """验证数据集质量"""
        dataset = self.get_object()
        
        # 这里应该实现数据质量验证逻辑
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [
                '发现5个缺失值',
                '检测到可能的异常值'
            ],
            'quality_score': 85.5
        }
        
        return Response(validation_result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """预览数据集内容"""
        dataset = self.get_object()
        
        # 这里应该实现数据预览逻辑
        preview_data = {
            'columns': ['feature1', 'feature2', 'feature3', 'target'],
            'data': [
                [1.2, 3.4, 5.6, 'A'],
                [2.3, 4.5, 6.7, 'B'],
                [3.4, 5.6, 7.8, 'A']
            ],
            'total_rows': dataset.size if dataset.size else 0,
            'preview_rows': 3
        }
        
        return Response(preview_data, status=status.HTTP_200_OK)


class DataProcessingTaskViewSet(viewsets.ModelViewSet):
    """数据处理任务ViewSet"""
    queryset = DataProcessingTask.objects.all()
    serializer_class = DataProcessingTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'task_type', 'input_dataset']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'started_at', 'finished_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return DataProcessingTask.objects.all()
        return DataProcessingTask.objects.filter(creator=user)

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """启动数据处理任务"""
        task = self.get_object()
        
        if task.status == 'running':
            return Response({
                'error': '任务已在运行中'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 这里应该实现具体的任务启动逻辑
        task.status = 'running'
        task.started_at = pd.Timestamp.now()
        task.save()
        
        return Response({
            'message': '任务启动成功',
            'task_id': task.id,
            'status': task.status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止数据处理任务"""
        task = self.get_object()
        
        if task.status != 'running':
            return Response({
                'error': '任务未在运行中'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'stopped'
        task.finished_at = pd.Timestamp.now()
        task.save()
        
        return Response({
            'message': '任务停止成功',
            'task_id': task.id,
            'status': task.status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取任务日志"""
        task = self.get_object()
        
        # 这里应该实现日志获取逻辑
        logs = task.logs if hasattr(task, 'logs') else '暂无日志'
        
        return Response({
            'logs': logs,
            'task_id': task.id,
            'status': task.status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """获取任务进度"""
        task = self.get_object()
        
        # 这里应该实现进度获取逻辑
        if task.status == 'completed':
            progress = 100
        elif task.status == 'running':
            progress = 50  # 模拟进度
        else:
            progress = 0
        
        return Response({
            'progress': progress,
            'status': task.status,
            'message': f'任务{task.status}'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """获取任务结果"""
        task = self.get_object()
        
        if task.status != 'completed':
            return Response({
                'error': '任务尚未完成'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 这里应该返回实际的处理结果
        result = {
            'output_dataset_id': None,  # 输出数据集ID
            'processing_summary': {
                'rows_processed': 1000,
                'rows_output': 950,
                'processing_time': '2.5 seconds'
            },
            'metrics': {
                'data_quality_score': 92.5,
                'missing_values_handled': 50,
                'outliers_detected': 5
            }
        }
        
        return Response(result, status=status.HTTP_200_OK)
