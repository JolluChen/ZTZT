from django.db import models
from django.conf import settings


class DataSource(models.Model):
    """数据源"""
    SOURCE_TYPES = [
        ('database', '数据库'),
        ('file', '文件'),
        ('api', 'API'),
        ('stream', '流数据'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='数据源名称')
    description = models.TextField(blank=True, verbose_name='描述')
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES, verbose_name='数据源类型')
    connection_info = models.JSONField(verbose_name='连接信息')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    tags = models.JSONField(default=list, verbose_name='标签')
    
    class Meta:
        verbose_name = '数据源'
        verbose_name_plural = '数据源'
        db_table = 'data_sources'
    
    def __str__(self):
        return self.name


class Dataset(models.Model):
    """数据集"""
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('parquet', 'Parquet'),
        ('excel', 'Excel'),
        ('txt', 'Text'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='数据集名称')
    description = models.TextField(blank=True, verbose_name='描述')
    file = models.FileField(upload_to='datasets/', verbose_name='数据文件')
    format = models.CharField(max_length=50, choices=FORMAT_CHOICES, verbose_name='数据格式')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    size_bytes = models.BigIntegerField(null=True, blank=True, verbose_name='文件大小(字节)')
    row_count = models.IntegerField(null=True, blank=True, verbose_name='行数')
    schema_info = models.JSONField(default=dict, verbose_name='数据结构信息')
    metadata = models.JSONField(default=dict, verbose_name='元数据')
    tags = models.JSONField(default=list, verbose_name='标签')
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    version = models.CharField(max_length=50, default='1.0', verbose_name='版本')
    
    class Meta:
        verbose_name = '数据集'
        verbose_name_plural = '数据集'
        db_table = 'datasets'
    
    def __str__(self):
        return f"{self.name} (v{self.version})"


class DataProcessingTask(models.Model):
    """数据处理任务"""
    TASK_TYPES = [
        ('etl', 'ETL处理'),
        ('clean', '数据清洗'),
        ('transform', '数据转换'),
        ('analysis', '数据分析'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='任务名称')
    description = models.TextField(blank=True, verbose_name='描述')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, verbose_name='任务类型')
    source_dataset = models.ForeignKey(
        Dataset, 
        on_delete=models.CASCADE, 
        related_name='processing_tasks',
        verbose_name='源数据集'
    )
    configuration = models.JSONField(verbose_name='任务配置')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    status_message = models.TextField(blank=True, verbose_name='状态信息')
    result_data = models.JSONField(default=dict, verbose_name='结果数据')
    
    class Meta:
        verbose_name = '数据处理任务'
        verbose_name_plural = '数据处理任务'
        db_table = 'data_processing_tasks'
    
    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
