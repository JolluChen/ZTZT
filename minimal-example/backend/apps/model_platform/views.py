import uuid
import json
from datetime import datetime
from django.utils import timezone
from django.db import models
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.parsers import MultiPartParser, FormParser

from .models import MLModel, ModelVersion, ModelEndpoint, ModelPrediction, ModelRegistry
from .serializers import (
    MLModelSerializer, ModelVersionSerializer, ModelEndpointSerializer,
    ModelPredictionSerializer, ModelRegistrySerializer, ModelCreateSerializer,
    ModelVersionCreateSerializer, ModelPredictionCreateSerializer
)


class MLModelViewSet(viewsets.ModelViewSet):
    """机器学习模型ViewSet"""
    queryset = MLModel.objects.all()
    serializer_class = MLModelSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model_type', 'status', 'framework']
    search_fields = ['name', 'description', 'model_type']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return MLModel.objects.all()
        return MLModel.objects.filter(creator=user)

    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'create':
            return ModelCreateSerializer
        return MLModelSerializer

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """部署模型"""
        model = self.get_object()
        
        if model.status == 'deployed':
            return Response({
                'error': '模型已经部署'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建模型端点
        endpoint = ModelEndpoint.objects.create(
            model=model,
            endpoint_url=f"/api/models/{model.id}/predict/",
            status='active'
        )
        
        model.status = 'deployed'
        model.save()
        
        return Response({
            'message': '模型部署成功',
            'endpoint_id': endpoint.id,
            'endpoint_url': endpoint.endpoint_url
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def undeploy(self, request, pk=None):
        """撤销模型部署"""
        model = self.get_object()
        
        if model.status != 'deployed':
            return Response({
                'error': '模型未部署'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 停用所有端点
        model.endpoints.update(status='inactive')
        model.status = 'ready'
        model.save()
        
        return Response({
            'message': '模型撤销部署成功'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def predict(self, request, pk=None):
        """模型预测"""
        model = self.get_object()
        
        if model.status != 'deployed':
            return Response({
                'error': '模型未部署'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        input_data = request.data.get('input_data', {})
        
        # 这里应该实现具体的预测逻辑
        # 目前返回模拟预测结果
        prediction_result = {
            'prediction': [0.85, 0.15],  # 模拟预测概率
            'confidence': 0.92,
            'model_version': model.versions.filter(is_active=True).first().version if model.versions.filter(is_active=True).exists() else '1.0.0'
        }
        
        # 记录预测历史
        ModelPrediction.objects.create(
            model=model,
            input_data=input_data,
            output_data=prediction_result,
            confidence_score=prediction_result['confidence']
        )
        
        return Response(prediction_result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """获取模型指标"""
        model = self.get_object()
        
        # 这里应该实现具体的指标计算逻辑
        metrics = {
            'accuracy': 0.95,
            'precision': 0.92,
            'recall': 0.88,
            'f1_score': 0.90,
            'auc': 0.96,
            'prediction_count': model.predictions.count(),
            'avg_confidence': 0.89
        }
        
        return Response(metrics, status=status.HTTP_200_OK)


class ModelVersionViewSet(viewsets.ModelViewSet):
    """模型版本ViewSet"""
    queryset = ModelVersion.objects.all()
    serializer_class = ModelVersionSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model', 'is_active']
    search_fields = ['version', 'description']
    ordering_fields = ['created_at', 'version']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return ModelVersion.objects.all()
        return ModelVersion.objects.filter(model__creator=user)

    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'create':
            return ModelVersionCreateSerializer
        return ModelVersionSerializer

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活模型版本"""
        version = self.get_object()
        
        # 先停用其他版本
        version.model.versions.update(is_active=False)
        
        # 激活当前版本
        version.is_active = True
        version.save()
        
        return Response({
            'message': f'版本 {version.version} 已激活'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        """版本比较"""
        version1 = self.get_object()
        version2_id = request.query_params.get('compare_with')
        
        if not version2_id:
            return Response({
                'error': '请提供要比较的版本ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            version2 = ModelVersion.objects.get(id=version2_id, model=version1.model)
        except ModelVersion.DoesNotExist:
            return Response({
                'error': '比较版本不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        comparison = {
            'version1': {
                'version': version1.version,
                'metrics': version1.metrics or {},
                'created_at': version1.created_at.isoformat()
            },
            'version2': {
                'version': version2.version,
                'metrics': version2.metrics or {},
                'created_at': version2.created_at.isoformat()
            },
            'comparison_summary': '版本1在准确率上更优'  # 模拟比较结果
        }
        
        return Response(comparison, status=status.HTTP_200_OK)


class ModelEndpointViewSet(viewsets.ModelViewSet):
    """模型端点ViewSet"""
    queryset = ModelEndpoint.objects.all()
    serializer_class = ModelEndpointSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model', 'status']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return ModelEndpoint.objects.all()
        return ModelEndpoint.objects.filter(model__creator=user)

    @action(detail=True, methods=['get'])
    def health(self, request, pk=None):
        """端点健康检查"""
        endpoint = self.get_object()
        
        # 这里应该实现具体的健康检查逻辑
        health_status = {
            'status': 'healthy' if endpoint.status == 'active' else 'unhealthy',
            'response_time': '50ms',
            'last_check': timezone.now().isoformat(),
            'uptime': '99.9%'
        }
        
        return Response(health_status, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """端点统计信息"""
        endpoint = self.get_object()
        
        stats = {
            'total_requests': 1250,  # 模拟数据
            'successful_requests': 1230,
            'failed_requests': 20,
            'avg_response_time': '45ms',
            'requests_per_minute': 25.5,
            'peak_requests_per_minute': 85
        }
        
        return Response(stats, status=status.HTTP_200_OK)


class ModelPredictionViewSet(viewsets.ModelViewSet):
    """模型预测ViewSet"""
    queryset = ModelPrediction.objects.all()
    serializer_class = ModelPredictionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['model']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']

    def get_queryset(self):
        """根据用户权限过滤查询集"""
        user = self.request.user
        if user.is_superuser:
            return ModelPrediction.objects.all()
        return ModelPrediction.objects.filter(model__creator=user)

    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'create':
            return ModelPredictionCreateSerializer
        return ModelPredictionSerializer

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """预测分析"""
        user = request.user
        predictions = self.get_queryset()
        
        analytics = {
            'total_predictions': predictions.count(),
            'avg_confidence': predictions.aggregate(
                avg_conf=models.Avg('confidence_score')
            )['avg_conf'] or 0,
            'predictions_by_model': {},
            'daily_predictions': {}  # 可以添加按日期的统计
        }
        
        return Response(analytics, status=status.HTTP_200_OK)


class ModelRegistryViewSet(viewsets.ModelViewSet):
    """模型注册表ViewSet"""
    queryset = ModelRegistry.objects.all()
    serializer_class = ModelRegistrySerializer
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
            return ModelRegistry.objects.all()
        # 用户可以看到公开的模型和自己创建的模型
        return ModelRegistry.objects.filter(
            models.Q(is_public=True) | models.Q(creator=user)
        )

    def perform_create(self, serializer):
        """创建时设置创建者"""
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def register_model(self, request, pk=None):
        """注册模型到注册表"""
        registry = self.get_object()
        model_id = request.data.get('model_id')
        
        if not model_id:
            return Response({
                'error': '请提供模型ID'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            model = MLModel.objects.get(id=model_id, creator=request.user)
            registry.models.add(model)
            
            return Response({
                'message': '模型注册成功',
                'model_id': model.id,
                'registry_id': registry.id
            }, status=status.HTTP_200_OK)
        except MLModel.DoesNotExist:
            return Response({
                'error': '模型不存在或无权限'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def search_models(self, request, pk=None):
        """在注册表中搜索模型"""
        registry = self.get_object()
        query = request.query_params.get('q', '')
        
        models = registry.models.filter(
            models.Q(name__icontains=query) | 
            models.Q(description__icontains=query)
        )
        
        results = []
        for model in models:
            results.append({
                'id': model.id,
                'name': model.name,
                'description': model.description,
                'model_type': model.model_type,
                'status': model.status
            })
        
        return Response({
            'query': query,
            'results': results,
            'total': len(results)
        }, status=status.HTTP_200_OK)
