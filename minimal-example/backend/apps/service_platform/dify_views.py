"""
Dify 集成视图
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.db import models
from django.utils import timezone
from datetime import timedelta
import requests
import json

from .models import DifyApplication, DifyConversation, DifyDataset
from .serializers import (
    DifyApplicationSerializer, DifyApplicationDetailSerializer,
    DifyConversationSerializer, DifyDatasetSerializer, DifyDatasetDetailSerializer
)


class DifyApplicationViewSet(viewsets.ModelViewSet):
    """Dify 应用管理"""
    queryset = DifyApplication.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DifyApplicationDetailSerializer
        return DifyApplicationSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        queryset = DifyApplication.objects.all()
        
        # 过滤条件
        app_type = self.request.query_params.get('app_type')
        is_active = self.request.query_params.get('is_active')
        is_public = self.request.query_params.get('is_public')
        search = self.request.query_params.get('search')
        
        if app_type:
            queryset = queryset.filter(app_type=app_type)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_public is not None:
            queryset = queryset.filter(is_public=is_public.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def chat(self, request, pk=None):
        """发送聊天消息到 Dify"""
        app = self.get_object()
        message = request.data.get('message', '')
        conversation_id = request.data.get('conversation_id', '')
        user_id = str(request.user.id)
        
        if not message:
            return Response(
                {'error': '消息不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 构建 Dify API 请求
        dify_api_url = f"{app.api_url or 'http://dify-nginx'}/v1/chat-messages"
        headers = {
            'Authorization': f'Bearer {app.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {},
            'query': message,
            'response_mode': 'blocking',
            'conversation_id': conversation_id,
            'user': user_id
        }
        
        try:
            response = requests.post(dify_api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 保存或更新对话记录
            if result.get('conversation_id'):
                conversation, created = DifyConversation.objects.get_or_create(
                    application=app,
                    user=request.user,
                    conversation_id=result['conversation_id'],
                    defaults={
                        'title': message[:50] if created else None,
                        'message_count': 1,
                        'token_count': result.get('metadata', {}).get('usage', {}).get('total_tokens', 0)
                    }
                )
                
                if not created:
                    conversation.message_count += 1
                    conversation.token_count += result.get('metadata', {}).get('usage', {}).get('total_tokens', 0)
                    conversation.save()
            
            return Response(result)
            
        except requests.exceptions.RequestException as e:
            return Response(
                {'error': f'Dify API 请求失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def conversations(self, request, pk=None):
        """获取应用的对话列表"""
        app = self.get_object()
        conversations = app.conversations.filter(user=request.user)
        
        # 分页
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = conversations.count()
        conversations = conversations[start:end]
        
        serializer = DifyConversationSerializer(conversations, many=True)
        
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def deploy(self, request, pk=None):
        """部署 Dify 应用"""
        app = self.get_object()
        
        # 这里可以添加部署逻辑
        # 例如：创建 Kubernetes 部署、配置负载均衡等
        
        app.is_active = True
        app.save()
        
        return Response({
            'message': '应用部署成功',
            'app_id': app.dify_app_id,
            'chat_url': app.chat_url
        })
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """停止 Dify 应用"""
        app = self.get_object()
        
        app.is_active = False
        app.save()
        
        return Response({'message': '应用已停止'})
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取应用统计信息"""
        app = self.get_object()
        
        # 统计数据
        total_conversations = app.conversations.count()
        total_messages = app.conversations.aggregate(
            total=models.Sum('message_count')
        )['total'] or 0
        total_tokens = app.conversations.aggregate(
            total=models.Sum('token_count')
        )['total'] or 0
        
        # 最近7天的对话数量
        week_ago = timezone.now() - timedelta(days=7)
        recent_conversations = app.conversations.filter(
            created_at__gte=week_ago
        ).count()
        
        # 活跃用户数
        active_users = app.conversations.values('user').distinct().count()
        
        return Response({
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'total_tokens': total_tokens,
            'recent_conversations': recent_conversations,
            'active_users': active_users,
            'is_active': app.is_active,
            'app_type': app.app_type
        })


class DifyConversationViewSet(viewsets.ModelViewSet):
    """Dify 对话管理"""
    queryset = DifyConversation.objects.all()
    serializer_class = DifyConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DifyConversation.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """置顶对话"""
        conversation = self.get_object()
        conversation.is_pinned = not conversation.is_pinned
        conversation.save()
        
        return Response({
            'is_pinned': conversation.is_pinned,
            'message': '置顶成功' if conversation.is_pinned else '取消置顶成功'
        })
    
    @action(detail=True, methods=['post'])
    def rename(self, request, pk=None):
        """重命名对话"""
        conversation = self.get_object()
        new_title = request.data.get('title', '').strip()
        
        if not new_title:
            return Response(
                {'error': '标题不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        conversation.title = new_title
        conversation.save()
        
        return Response({'message': '重命名成功', 'title': new_title})


class DifyDatasetViewSet(viewsets.ModelViewSet):
    """Dify 知识库管理"""
    queryset = DifyDataset.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DifyDatasetDetailSerializer
        return DifyDatasetSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        queryset = DifyDataset.objects.all()
        
        # 过滤条件
        index_type = self.request.query_params.get('index_type')
        search = self.request.query_params.get('search')
        
        if index_type:
            queryset = queryset.filter(index_type=index_type)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def upload_document(self, request, pk=None):
        """上传文档到知识库"""
        dataset = self.get_object()
        file = request.FILES.get('file')
        
        if not file:
            return Response(
                {'error': '请选择要上传的文件'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 这里可以调用 Dify API 上传文档
        # 或者保存到本地再同步到 Dify
        
        return Response({
            'message': '文档上传成功',
            'file_name': file.name,
            'dataset_id': dataset.dify_dataset_id
        })
    
    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """获取知识库文档列表"""
        dataset = self.get_object()
        
        # 这里可以调用 Dify API 获取文档列表
        # 暂时返回模拟数据
        
        return Response({
            'dataset_id': dataset.dify_dataset_id,
            'documents': [],
            'total': dataset.document_count
        })
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """同步知识库状态"""
        dataset = self.get_object()
        
        # 这里可以调用 Dify API 同步知识库状态
        # 更新文档数量、字符数量等信息
        
        return Response({
            'message': '同步成功',
            'document_count': dataset.document_count,
            'character_count': dataset.character_count
        })
