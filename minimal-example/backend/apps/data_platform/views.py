from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# 临时模拟数据，稍后可以连接真实数据库
MOCK_DATA_SOURCES = [
    {'id': 1, 'name': 'Sales Database', 'type': 'database', 'status': 'active'},
    {'id': 2, 'name': 'User Analytics', 'type': 'api', 'status': 'active'},
    {'id': 3, 'name': 'Log Files', 'type': 'file', 'status': 'inactive'},
]

MOCK_DATASETS = [
    {'id': 1, 'name': 'Customer Dataset', 'size': '1.2GB', 'format': 'CSV'},
    {'id': 2, 'name': 'Product Dataset', 'size': '800MB', 'format': 'JSON'},
    {'id': 3, 'name': 'Analytics Dataset', 'size': '2.1GB', 'format': 'Parquet'},
]

MOCK_PROCESSING_TASKS = [
    {'id': 1, 'name': 'Data Cleaning Task', 'status': 'completed', 'progress': 100},
    {'id': 2, 'name': 'Feature Engineering', 'status': 'running', 'progress': 65},
    {'id': 3, 'name': 'Data Validation', 'status': 'pending', 'progress': 0},
]

class DataSourceViewSet(viewsets.ViewSet):
    """数据源管理ViewSet"""
    
    def list(self, request):
        """获取数据源列表"""
        return Response({
            'count': len(MOCK_DATA_SOURCES),
            'results': MOCK_DATA_SOURCES
        })
    
    def create(self, request):
        """创建数据源"""
        return Response({
            'message': '数据源创建功能开发中',
            'data': request.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """获取单个数据源"""
        for item in MOCK_DATA_SOURCES:
            if item['id'] == int(pk):
                return Response(item)
        return Response({'error': '数据源未找到'}, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, pk=None):
        """更新数据源"""
        return Response({
            'message': f'数据源 {pk} 更新功能开发中',
            'data': request.data
        })
    
    def destroy(self, request, pk=None):
        """删除数据源"""
        return Response({
            'message': f'数据源 {pk} 删除功能开发中'
        })
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """测试数据源连接"""
        return Response({
            'status': 'success',
            'message': '连接测试成功'
        })

class DatasetViewSet(viewsets.ViewSet):
    """数据集管理ViewSet"""
    
    def list(self, request):
        """获取数据集列表"""
        return Response({
            'count': len(MOCK_DATASETS),
            'results': MOCK_DATASETS
        })
    
    def create(self, request):
        """创建数据集"""
        return Response({
            'message': '数据集创建功能开发中',
            'data': request.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """获取单个数据集"""
        for item in MOCK_DATASETS:
            if item['id'] == int(pk):
                return Response(item)
        return Response({'error': '数据集未找到'}, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, pk=None):
        """更新数据集"""
        return Response({
            'message': f'数据集 {pk} 更新功能开发中',
            'data': request.data
        })
    
    def destroy(self, request, pk=None):
        """删除数据集"""
        return Response({
            'message': f'数据集 {pk} 删除功能开发中'
        })

class DataProcessingTaskViewSet(viewsets.ViewSet):
    """数据处理任务ViewSet"""
    
    def list(self, request):
        """获取处理任务列表"""
        return Response({
            'count': len(MOCK_PROCESSING_TASKS),
            'results': MOCK_PROCESSING_TASKS
        })
    
    def create(self, request):
        """创建处理任务"""
        return Response({
            'message': '数据处理任务创建功能开发中',
            'data': request.data
        }, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """获取单个处理任务"""
        for item in MOCK_PROCESSING_TASKS:
            if item['id'] == int(pk):
                return Response(item)
        return Response({'error': '处理任务未找到'}, status=status.HTTP_404_NOT_FOUND)
    
    def update(self, request, pk=None):
        """更新处理任务"""
        return Response({
            'message': f'处理任务 {pk} 更新功能开发中',
            'data': request.data
        })
    
    def destroy(self, request, pk=None):
        """删除处理任务"""
        return Response({
            'message': f'处理任务 {pk} 删除功能开发中'
        })
    
    @action(detail=True, methods=['post'])
    def start_task(self, request, pk=None):
        """启动处理任务"""
        return Response({
            'status': 'success',
            'message': f'任务 {pk} 已启动'
        })
    
    @action(detail=True, methods=['post'])
    def stop_task(self, request, pk=None):
        """停止处理任务"""
        return Response({
            'status': 'success',
            'message': f'任务 {pk} 已停止'
        })

# 保留原有的健康检查函数
@api_view(['GET'])
def data_health(request):
    """数据平台健康检查"""
    return JsonResponse({
        'status': 'ok',
        'service': 'data_platform',
        'message': 'Data platform is running'
    })
