"""
Dify 集成模型
"""
from django.db import models
from django.contrib.auth.models import User
from .base import BaseModel
import json


class DifyApplication(BaseModel):
    """Dify 应用模型"""
    
    APP_TYPES = [
        ('chat', '对话应用'),
        ('completion', '文本生成'),
        ('workflow', '工作流'),
        ('agent', '智能体'),
    ]
    
    MODES = [
        ('simple', '简单模式'),
        ('advanced', '高级模式'),
    ]
    
    # 基础信息
    name = models.CharField(max_length=255, verbose_name='应用名称')
    description = models.TextField(blank=True, verbose_name='应用描述')
    icon = models.URLField(blank=True, verbose_name='应用图标')
    
    # Dify 相关
    dify_app_id = models.CharField(max_length=255, unique=True, verbose_name='Dify应用ID')
    app_type = models.CharField(max_length=20, choices=APP_TYPES, verbose_name='应用类型')
    mode = models.CharField(max_length=20, choices=MODES, default='simple', verbose_name='应用模式')
    
    # 配置信息
    model_config = models.JSONField(default=dict, verbose_name='模型配置')
    prompt_config = models.JSONField(default=dict, verbose_name='提示词配置')
    conversation_config = models.JSONField(default=dict, verbose_name='对话配置')
    
    # API 配置
    api_key = models.CharField(max_length=255, blank=True, verbose_name='API密钥')
    api_url = models.URLField(blank=True, verbose_name='API地址')
    
    # 状态和权限
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    
    # 关联信息
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    
    class Meta:
        verbose_name = 'Dify应用'
        verbose_name_plural = 'Dify应用'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    @property
    def chat_url(self):
        """获取聊天界面URL"""
        return f"/dify/chat/{self.dify_app_id}"
    
    @property
    def api_endpoint(self):
        """获取API端点"""
        return f"/v1/chat-messages"


class DifyConversation(BaseModel):
    """Dify 对话记录"""
    
    application = models.ForeignKey(
        DifyApplication, 
        on_delete=models.CASCADE, 
        related_name='conversations',
        verbose_name='关联应用'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    
    # Dify 对话标识
    conversation_id = models.CharField(max_length=255, verbose_name='对话ID')
    
    # 对话信息
    title = models.CharField(max_length=255, blank=True, verbose_name='对话标题')
    summary = models.TextField(blank=True, verbose_name='对话摘要')
    
    # 统计信息
    message_count = models.IntegerField(default=0, verbose_name='消息数量')
    token_count = models.IntegerField(default=0, verbose_name='Token消耗')
    
    # 状态
    is_pinned = models.BooleanField(default=False, verbose_name='是否置顶')
    
    class Meta:
        verbose_name = 'Dify对话'
        verbose_name_plural = 'Dify对话'
        ordering = ['-updated_at']
        unique_together = ['application', 'conversation_id']
        
    def __str__(self):
        return f"{self.application.name} - {self.title or self.conversation_id[:8]}"


class DifyMessage(BaseModel):
    """Dify 消息记录"""
    
    MESSAGE_TYPES = [
        ('user', '用户消息'),
        ('assistant', '助手回复'),
        ('system', '系统消息'),
    ]
    
    conversation = models.ForeignKey(
        DifyConversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name='关联对话'
    )
    
    # 消息标识
    message_id = models.CharField(max_length=255, verbose_name='消息ID')
    
    # 消息内容
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, verbose_name='消息类型')
    content = models.TextField(verbose_name='消息内容')
    
    # 元数据
    metadata = models.JSONField(default=dict, verbose_name='消息元数据')
    
    # 统计信息
    token_count = models.IntegerField(default=0, verbose_name='Token数量')
    
    class Meta:
        verbose_name = 'Dify消息'
        verbose_name_plural = 'Dify消息'
        ordering = ['created_at']
        unique_together = ['conversation', 'message_id']
        
    def __str__(self):
        return f"{self.conversation} - {self.message_type}: {self.content[:50]}"


class DifyWorkflow(BaseModel):
    """Dify 工作流模型"""
    
    WORKFLOW_TYPES = [
        ('sequential', '顺序执行'),
        ('parallel', '并行执行'),
        ('conditional', '条件执行'),
        ('loop', '循环执行'),
    ]
    
    application = models.ForeignKey(
        DifyApplication, 
        on_delete=models.CASCADE, 
        related_name='workflows',
        verbose_name='关联应用'
    )
    
    # 工作流信息
    name = models.CharField(max_length=255, verbose_name='工作流名称')
    description = models.TextField(blank=True, verbose_name='工作流描述')
    workflow_type = models.CharField(max_length=20, choices=WORKFLOW_TYPES, verbose_name='工作流类型')
    
    # Dify 工作流配置
    dify_workflow_id = models.CharField(max_length=255, verbose_name='Dify工作流ID')
    workflow_config = models.JSONField(default=dict, verbose_name='工作流配置')
    
    # 版本控制
    version = models.CharField(max_length=50, default='1.0.0', verbose_name='版本号')
    
    # 状态
    is_published = models.BooleanField(default=False, verbose_name='是否发布')
    
    class Meta:
        verbose_name = 'Dify工作流'
        verbose_name_plural = 'Dify工作流'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.application.name} - {self.name}"


class DifyDataset(BaseModel):
    """Dify 知识库模型"""
    
    INDEX_TYPES = [
        ('high_quality', '高质量模式'),
        ('economy', '经济模式'),
    ]
    
    # 基础信息
    name = models.CharField(max_length=255, verbose_name='知识库名称')
    description = models.TextField(blank=True, verbose_name='知识库描述')
    
    # Dify 知识库信息
    dify_dataset_id = models.CharField(max_length=255, unique=True, verbose_name='Dify知识库ID')
    
    # 配置信息
    index_type = models.CharField(max_length=20, choices=INDEX_TYPES, default='high_quality', verbose_name='索引类型')
    embedding_model = models.CharField(max_length=255, blank=True, verbose_name='嵌入模型')
    
    # 统计信息
    document_count = models.IntegerField(default=0, verbose_name='文档数量')
    character_count = models.IntegerField(default=0, verbose_name='字符数量')
    
    # 关联信息
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    applications = models.ManyToManyField(
        DifyApplication, 
        through='DifyApplicationDataset',
        verbose_name='关联应用'
    )
    
    class Meta:
        verbose_name = 'Dify知识库'
        verbose_name_plural = 'Dify知识库'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name


class DifyApplicationDataset(BaseModel):
    """Dify 应用与知识库关联"""
    
    application = models.ForeignKey(DifyApplication, on_delete=models.CASCADE, verbose_name='应用')
    dataset = models.ForeignKey(DifyDataset, on_delete=models.CASCADE, verbose_name='知识库')
    
    # 配置信息
    retrieval_config = models.JSONField(default=dict, verbose_name='检索配置')
    
    class Meta:
        verbose_name = 'Dify应用知识库关联'
        verbose_name_plural = 'Dify应用知识库关联'
        unique_together = ['application', 'dataset']
        
    def __str__(self):
        return f"{self.application.name} - {self.dataset.name}"


class DifyAPIUsage(BaseModel):
    """Dify API 使用统计"""
    
    application = models.ForeignKey(
        DifyApplication, 
        on_delete=models.CASCADE, 
        related_name='api_usage',
        verbose_name='关联应用'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    
    # 统计信息
    request_count = models.IntegerField(default=0, verbose_name='请求次数')
    token_count = models.IntegerField(default=0, verbose_name='Token消耗')
    
    # 时间维度
    date = models.DateField(verbose_name='统计日期')
    hour = models.IntegerField(verbose_name='小时（0-23）')
    
    class Meta:
        verbose_name = 'Dify API使用统计'
        verbose_name_plural = 'Dify API使用统计'
        ordering = ['-date', '-hour']
        unique_together = ['application', 'user', 'date', 'hour']
        
    def __str__(self):
        return f"{self.application.name} - {self.date} {self.hour}:00"
