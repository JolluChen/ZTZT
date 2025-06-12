from django.db import models
from django.conf import settings
from apps.authentication.models import Organization
from apps.algorithm_platform.models import Experiment


class MLModel(models.Model):
    """机器学习模型"""
    name = models.CharField('模型名称', max_length=255)
    description = models.TextField('模型描述', blank=True)
    
    # 模型基本信息
    model_type = models.CharField('模型类型', max_length=50, choices=[
        ('classification', '分类模型'),
        ('regression', '回归模型'),
        ('clustering', '聚类模型'),
        ('deep_learning', '深度学习模型'),
        ('nlp', 'NLP模型'),
        ('computer_vision', '计算机视觉模型'),
        ('recommendation', '推荐模型'),
        ('time_series', '时间序列模型'),
        ('other', '其他')
    ])
    
    framework = models.CharField('模型框架', max_length=50, choices=[
        ('tensorflow', 'TensorFlow'),
        ('pytorch', 'PyTorch'),
        ('scikit-learn', 'Scikit-learn'),
        ('xgboost', 'XGBoost'),
        ('lightgbm', 'LightGBM'),
        ('onnx', 'ONNX'),
        ('other', '其他')
    ])
    
    # 模型来源
    source_experiment = models.ForeignKey(
        Experiment,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='来源实验'
    )
    
    # 模型状态
    status = models.CharField('状态', max_length=20, choices=[
        ('training', '训练中'),
        ('trained', '训练完成'),
        ('validated', '验证完成'),
        ('registered', '已注册'),
        ('deployed', '已部署'),
        ('archived', '已归档')
    ], default='training')
    
    # 系统字段
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        verbose_name='所属组织'
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='创建者'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'ml_models'
        verbose_name = '机器学习模型'
        verbose_name_plural = '机器学习模型'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ModelVersion(models.Model):
    """模型版本"""
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name='所属模型'
    )
    version = models.CharField('版本号', max_length=50)
    description = models.TextField('版本描述', blank=True)
    
    # 模型文件
    model_file = models.FileField('模型文件', upload_to='models/', null=True, blank=True)
    model_size = models.BigIntegerField('文件大小(字节)', null=True, blank=True)
    model_format = models.CharField('模型格式', max_length=50, choices=[
        ('pkl', 'Pickle'),
        ('h5', 'HDF5'),
        ('pb', 'TensorFlow SavedModel'),
        ('pth', 'PyTorch'),
        ('onnx', 'ONNX'),
        ('joblib', 'Joblib'),
        ('other', '其他')
    ], default='pkl')
    
    # 模型性能指标
    metrics = models.JSONField('性能指标', default=dict, blank=True)
    
    # 模型配置
    hyperparameters = models.JSONField('超参数', default=dict, blank=True)
    training_config = models.JSONField('训练配置', default=dict, blank=True)
    
    # 版本状态
    is_latest = models.BooleanField('是否最新版本', default=True)
    is_active = models.BooleanField('是否激活', default=True)
    
    # 时间字段
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'model_versions'
        verbose_name = '模型版本'
        verbose_name_plural = '模型版本'
        ordering = ['-created_at']
        unique_together = ['model', 'version']

    def __str__(self):
        return f"{self.model.name} v{self.version}"

    def save(self, *args, **kwargs):
        # 如果设置为最新版本，则将其他版本设置为非最新
        if self.is_latest:
            ModelVersion.objects.filter(model=self.model).update(is_latest=False)
        super().save(*args, **kwargs)


class ModelEndpoint(models.Model):
    """模型服务端点"""
    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.CASCADE,
        related_name='endpoints',
        verbose_name='模型版本'
    )
    name = models.CharField('端点名称', max_length=255)
    description = models.TextField('端点描述', blank=True)
    
    # 端点配置
    endpoint_url = models.URLField('端点URL', blank=True)
    api_key = models.CharField('API密钥', max_length=255, blank=True)
    
    # 部署配置
    deployment_config = models.JSONField('部署配置', default=dict, blank=True)
    resource_requirements = models.JSONField('资源需求', default=dict, blank=True)
    
    # 端点状态
    status = models.CharField('状态', max_length=20, choices=[
        ('creating', '创建中'),
        ('active', '运行中'),
        ('updating', '更新中'),
        ('inactive', '已停止'),
        ('failed', '失败'),
        ('deleted', '已删除')
    ], default='creating')
    
    # 监控信息
    health_check_url = models.URLField('健康检查URL', blank=True)
    last_health_check = models.DateTimeField('最后健康检查时间', null=True, blank=True)
    
    # 时间字段
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    deployed_at = models.DateTimeField('部署时间', null=True, blank=True)
    
    class Meta:
        db_table = 'model_endpoints'
        verbose_name = '模型端点'
        verbose_name_plural = '模型端点'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.model_version.model.name} - {self.name}"


class ModelPrediction(models.Model):
    """模型预测记录"""
    endpoint = models.ForeignKey(
        ModelEndpoint,
        on_delete=models.CASCADE,
        related_name='predictions',
        verbose_name='模型端点'
    )
    
    # 预测请求信息
    request_id = models.CharField('请求ID', max_length=100, unique=True)
    input_data = models.JSONField('输入数据', default=dict)
    output_data = models.JSONField('输出数据', default=dict)
    
    # 预测结果
    prediction_result = models.JSONField('预测结果', default=dict)
    confidence_score = models.FloatField('置信度', null=True, blank=True)
    
    # 性能指标
    latency_ms = models.IntegerField('延迟(毫秒)', null=True, blank=True)
    processing_time_ms = models.IntegerField('处理时间(毫秒)', null=True, blank=True)
    
    # 请求信息
    user_agent = models.CharField('用户代理', max_length=500, blank=True)
    ip_address = models.GenericIPAddressField('IP地址', null=True, blank=True)
    
    # 状态信息
    status = models.CharField('状态', max_length=20, choices=[
        ('success', '成功'),
        ('error', '错误'),
        ('timeout', '超时')
    ], default='success')
    error_message = models.TextField('错误信息', blank=True)
    
    # 时间字段
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'model_predictions'
        verbose_name = '模型预测记录'
        verbose_name_plural = '模型预测记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.endpoint.name} - {self.request_id}"


class ModelRegistry(models.Model):
    """模型注册表"""
    model = models.ForeignKey(
        MLModel,
        on_delete=models.CASCADE,
        related_name='registry_entries',
        verbose_name='模型'
    )
    
    # 注册信息
    registry_name = models.CharField('注册名称', max_length=255)
    registry_tags = models.JSONField('标签', default=list, blank=True)
    
    # 模型元数据
    model_schema = models.JSONField('模型架构', default=dict, blank=True)
    input_schema = models.JSONField('输入架构', default=dict, blank=True)
    output_schema = models.JSONField('输出架构', default=dict, blank=True)
    
    # 模型验证信息
    validation_dataset = models.CharField('验证数据集', max_length=255, blank=True)
    validation_metrics = models.JSONField('验证指标', default=dict, blank=True)
    
    # 注册状态
    is_public = models.BooleanField('是否公开', default=False)
    is_approved = models.BooleanField('是否审批通过', default=False)
    approval_notes = models.TextField('审批备注', blank=True)
    
    # 时间字段
    registered_at = models.DateTimeField('注册时间', auto_now_add=True)
    approved_at = models.DateTimeField('审批时间', null=True, blank=True)
    
    class Meta:
        db_table = 'model_registry'
        verbose_name = '模型注册表'
        verbose_name_plural = '模型注册表'
        ordering = ['-registered_at']
        unique_together = ['model', 'registry_name']

    def __str__(self):
        return f"{self.model.name} - {self.registry_name}"