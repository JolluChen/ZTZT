from django.db import models
from django.conf import settings
from apps.authentication.models import Organization
from apps.data_platform.models import Dataset


class AlgorithmProject(models.Model):
    """算法项目模型"""
    name = models.CharField('项目名称', max_length=255)
    description = models.TextField('项目描述', blank=True)
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
    is_active = models.BooleanField('是否激活', default=True)
    
    # 项目配置
    framework = models.CharField('算法框架', max_length=50, choices=[
        ('tensorflow', 'TensorFlow'),
        ('pytorch', 'PyTorch'),
        ('scikit-learn', 'Scikit-learn'),
        ('xgboost', 'XGBoost'),
        ('other', '其他')
    ], default='tensorflow')
    
    environment_config = models.JSONField('环境配置', default=dict, blank=True)
    git_repository = models.URLField('Git仓库', blank=True)
    
    class Meta:
        db_table = 'algorithm_projects'
        verbose_name = '算法项目'
        verbose_name_plural = '算法项目'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Experiment(models.Model):
    """实验模型"""
    project = models.ForeignKey(
        AlgorithmProject, 
        on_delete=models.CASCADE, 
        related_name='experiments',
        verbose_name='所属项目'
    )
    name = models.CharField('实验名称', max_length=255)
    description = models.TextField('实验描述', blank=True)
    
    # 实验配置
    algorithm_type = models.CharField('算法类型', max_length=50, choices=[
        ('classification', '分类'),
        ('regression', '回归'),
        ('clustering', '聚类'),
        ('deep_learning', '深度学习'),
        ('nlp', '自然语言处理'),
        ('computer_vision', '计算机视觉'),
        ('other', '其他')
    ])
    
    dataset = models.ForeignKey(
        Dataset, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        verbose_name='训练数据集'
    )
    
    # 超参数配置
    hyperparameters = models.JSONField('超参数', default=dict, blank=True)
    
    # 实验状态
    status = models.CharField('状态', max_length=20, choices=[
        ('created', '已创建'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('stopped', '已停止')
    ], default='created')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name='创建者'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    
    class Meta:
        db_table = 'algorithm_experiments'
        verbose_name = '算法实验'
        verbose_name_plural = '算法实验'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ExperimentRun(models.Model):
    """实验运行记录模型"""
    experiment = models.ForeignKey(
        Experiment, 
        on_delete=models.CASCADE, 
        related_name='runs',
        verbose_name='所属实验'
    )
    run_id = models.CharField('运行ID', max_length=100, unique=True)
    version = models.IntegerField('版本号', default=1)
    
    # 运行配置
    parameters = models.JSONField('运行参数', default=dict, blank=True)
    
    # 运行结果
    metrics = models.JSONField('评估指标', default=dict, blank=True)
    artifacts = models.JSONField('产出文件', default=dict, blank=True)
    
    # 运行状态
    status = models.CharField('状态', max_length=20, choices=[
        ('queued', '排队中'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('killed', '已终止')
    ], default='queued')
    
    # 时间记录
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    ended_at = models.DateTimeField('结束时间', null=True, blank=True)
    duration = models.DurationField('运行时长', null=True, blank=True)
    
    # 资源使用
    resource_usage = models.JSONField('资源使用情况', default=dict, blank=True)
    
    # 日志和错误信息
    logs = models.TextField('运行日志', blank=True)
    error_message = models.TextField('错误信息', blank=True)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'algorithm_experiment_runs'
        verbose_name = '实验运行记录'
        verbose_name_plural = '实验运行记录'
        ordering = ['-created_at']
        unique_together = ['experiment', 'version']

    def __str__(self):
        return f"{self.experiment.name} - Run {self.version}"


class Algorithm(models.Model):
    """算法模板模型"""
    name = models.CharField('算法名称', max_length=255)
    description = models.TextField('算法描述')
    category = models.CharField('算法分类', max_length=50, choices=[
        ('classification', '分类'),
        ('regression', '回归'),
        ('clustering', '聚类'),
        ('deep_learning', '深度学习'),
        ('nlp', '自然语言处理'),
        ('computer_vision', '计算机视觉'),
        ('recommendation', '推荐系统'),
        ('time_series', '时间序列'),
        ('other', '其他')
    ])
    
    # 算法实现
    framework = models.CharField('算法框架', max_length=50)
    code_template = models.TextField('代码模板')
    default_parameters = models.JSONField('默认参数', default=dict)
    
    # 算法元信息
    author = models.CharField('作者', max_length=255, blank=True)
    version = models.CharField('版本', max_length=50, default='1.0.0')
    documentation = models.TextField('文档说明', blank=True)
    
    # 系统字段
    is_builtin = models.BooleanField('是否内置', default=True)
    is_active = models.BooleanField('是否激活', default=True)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        null=True, blank=True,
        verbose_name='所属组织'
    )
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'algorithms'
        verbose_name = '算法模板'
        verbose_name_plural = '算法模板'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
