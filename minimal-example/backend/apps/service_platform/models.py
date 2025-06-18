"""
服务中台模型定义
负责AI应用编排、服务发布、版本管理和服务监控
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json


class ServiceCategory(models.Model):
    """服务分类"""
    name = models.CharField(max_length=100, verbose_name="分类名称")
    description = models.TextField(blank=True, verbose_name="描述")
    icon = models.CharField(max_length=50, blank=True, verbose_name="图标")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "服务分类"
        verbose_name_plural = verbose_name
        
    def __str__(self):
        return self.name


class Application(models.Model):
    """AI应用"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('developing', '开发中'),
        ('testing', '测试中'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]
    
    TYPE_CHOICES = [
        ('web_service', 'Web服务'),
        ('api_service', 'API服务'),
        ('batch_job', '批处理任务'),
        ('stream_processing', '流处理'),
        ('ml_inference', '机器学习推理'),
        ('data_processing', '数据处理'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="应用名称")
    display_name = models.CharField(max_length=200, verbose_name="显示名称")
    description = models.TextField(verbose_name="应用描述")
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, verbose_name="分类")
    
    # 应用配置
    app_type = models.CharField(max_length=50, choices=TYPE_CHOICES, verbose_name="应用类型")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="状态")
    version = models.CharField(max_length=50, default='1.0.0', verbose_name="当前版本")
    
    # 组件配置
    components = models.JSONField(default=dict, verbose_name="组件配置", help_text="应用包含的各种组件配置")
    dependencies = models.JSONField(default=list, verbose_name="依赖配置", help_text="应用依赖的其他服务或模型")
    
    # 元数据
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 统计信息
    view_count = models.PositiveIntegerField(default=0, verbose_name="查看次数")
    deployment_count = models.PositiveIntegerField(default=0, verbose_name="部署次数")
    
    class Meta:
        verbose_name = "AI应用"
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.display_name} ({self.version})"


class ApplicationVersion(models.Model):
    """应用版本"""
    STATUS_CHOICES = [
        ('building', '构建中'),
        ('build_failed', '构建失败'),
        ('ready', '就绪'),
        ('deploying', '部署中'),
        ('deployed', '已部署'),
        ('failed', '失败'),
        ('deprecated', '已废弃'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='versions', verbose_name="应用")
    version = models.CharField(max_length=50, verbose_name="版本号")
    description = models.TextField(blank=True, verbose_name="版本描述")
    
    # 版本配置
    config = models.JSONField(default=dict, verbose_name="配置信息")
    dockerfile = models.TextField(blank=True, verbose_name="Dockerfile内容")
    requirements = models.TextField(blank=True, verbose_name="依赖要求")
    
    # 部署信息
    image_url = models.CharField(max_length=500, blank=True, verbose_name="镜像地址")
    manifest = models.JSONField(default=dict, verbose_name="Kubernetes清单")
    
    # 状态和元数据
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='building', verbose_name="状态")
    build_log = models.TextField(blank=True, verbose_name="构建日志")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "应用版本"
        verbose_name_plural = verbose_name
        unique_together = [['application', 'version']]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.application.name} v{self.version}"


class ServiceEndpoint(models.Model):
    """服务端点"""
    PROTOCOL_CHOICES = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
        ('grpc', 'gRPC'),
        ('tcp', 'TCP'),
        ('udp', 'UDP'),
    ]
    
    STATUS_CHOICES = [
        ('starting', '启动中'),
        ('running', '运行中'),
        ('stopping', '停止中'),
        ('stopped', '已停止'),
        ('error', '错误'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_version = models.ForeignKey(ApplicationVersion, on_delete=models.CASCADE, related_name='endpoints', verbose_name="应用版本")
    
    # 端点信息
    name = models.CharField(max_length=200, verbose_name="端点名称")
    protocol = models.CharField(max_length=10, choices=PROTOCOL_CHOICES, default='http', verbose_name="协议")
    host = models.CharField(max_length=255, verbose_name="主机地址")
    port = models.PositiveIntegerField(verbose_name="端口")
    path = models.CharField(max_length=500, default='/', verbose_name="路径")
    
    # 状态和配置
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='starting', verbose_name="状态")
    replicas = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)], verbose_name="副本数")
    
    # 健康检查
    health_check_path = models.CharField(max_length=200, default='/health', verbose_name="健康检查路径")
    last_health_check = models.DateTimeField(null=True, blank=True, verbose_name="最后健康检查时间")
    is_healthy = models.BooleanField(default=False, verbose_name="是否健康")
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "服务端点"
        verbose_name_plural = verbose_name
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({self.protocol}://{self.host}:{self.port})"
    
    @property
    def url(self):
        """完整URL"""
        return f"{self.protocol}://{self.host}:{self.port}{self.path}"


class ServiceMonitoring(models.Model):
    """服务监控"""
    endpoint = models.ForeignKey(ServiceEndpoint, on_delete=models.CASCADE, related_name='monitoring_data', verbose_name="服务端点")
    
    # 性能指标
    cpu_usage = models.FloatField(verbose_name="CPU使用率(%)")
    memory_usage = models.FloatField(verbose_name="内存使用率(%)")
    request_count = models.PositiveIntegerField(default=0, verbose_name="请求数")
    error_count = models.PositiveIntegerField(default=0, verbose_name="错误数")
    response_time = models.FloatField(verbose_name="响应时间(ms)")
    
    # 网络指标
    network_in = models.FloatField(default=0, verbose_name="网络入流量(MB)")
    network_out = models.FloatField(default=0, verbose_name="网络出流量(MB)")
    
    # 业务指标
    custom_metrics = models.JSONField(default=dict, verbose_name="自定义指标")
    
    # 时间戳
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="时间戳")
    
    class Meta:
        verbose_name = "服务监控"
        verbose_name_plural = verbose_name
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['endpoint', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        
    def __str__(self):
        return f"{self.endpoint.name} - {self.timestamp}"


class ServiceTemplate(models.Model):
    """服务模板"""
    TEMPLATE_TYPE_CHOICES = [
        ('web_api', 'Web API模板'),
        ('ml_service', '机器学习服务模板'),
        ('data_pipeline', '数据管道模板'),
        ('microservice', '微服务模板'),
        ('batch_job', '批处理作业模板'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="模板名称")
    description = models.TextField(verbose_name="模板描述")
    template_type = models.CharField(max_length=50, choices=TEMPLATE_TYPE_CHOICES, verbose_name="模板类型")
    
    # 模板配置
    config_schema = models.JSONField(default=dict, verbose_name="配置模式")
    default_config = models.JSONField(default=dict, verbose_name="默认配置")
    dockerfile_template = models.TextField(verbose_name="Dockerfile模板")
    manifest_template = models.JSONField(default=dict, verbose_name="Kubernetes清单模板")
    
    # 元数据
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="创建者")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True, verbose_name="是否公开")
    usage_count = models.PositiveIntegerField(default=0, verbose_name="使用次数")
    
    class Meta:
        verbose_name = "服务模板"
        verbose_name_plural = verbose_name
        ordering = ['-usage_count', 'name']
        
    def __str__(self):
        return self.name


class ServiceAlert(models.Model):
    """服务告警"""
    LEVEL_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('critical', '严重'),
    ]
    
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('resolved', '已解决'),
        ('acknowledged', '已确认'),
        ('ignored', '已忽略'),
    ]
    
    endpoint = models.ForeignKey(ServiceEndpoint, on_delete=models.CASCADE, related_name='alerts', verbose_name="服务端点")
    
    # 告警信息
    title = models.CharField(max_length=200, verbose_name="告警标题")
    message = models.TextField(verbose_name="告警消息")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, verbose_name="告警级别")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="状态")
    
    # 规则和条件
    rule_name = models.CharField(max_length=200, verbose_name="规则名称")
    condition = models.JSONField(default=dict, verbose_name="触发条件")
    
    # 时间信息
    triggered_at = models.DateTimeField(auto_now_add=True, verbose_name="触发时间")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="解决时间")
    acknowledged_at = models.DateTimeField(null=True, blank=True, verbose_name="确认时间")
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="确认人")
    
    class Meta:
        verbose_name = "服务告警"
        verbose_name_plural = verbose_name
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['status', '-triggered_at']),
            models.Index(fields=['level', '-triggered_at']),
        ]
        
    def __str__(self):
        return f"{self.title} - {self.level}"


# ====== Dify 集成模型 ======

class DifyApplication(models.Model):
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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
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


class DifyConversation(models.Model):
    """Dify 对话记录"""
    
    application = models.ForeignKey(
        DifyApplication, 
        on_delete=models.CASCADE, 
        related_name='conversations',
        verbose_name='关联应用'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    
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
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Dify对话'
        verbose_name_plural = 'Dify对话'
        ordering = ['-updated_at']
        unique_together = ['application', 'conversation_id']
        
    def __str__(self):
        return f"{self.application.name} - {self.title or self.conversation_id[:8]}"


class DifyDataset(models.Model):
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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Dify知识库'
        verbose_name_plural = 'Dify知识库'
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
