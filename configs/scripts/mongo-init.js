db = db.getSiblingDB('ai_platform');

db.createUser({
  user: 'ai_platform_user',
  pwd: 'changeThisToSecurePassword',
  roles: [
    { role: 'readWrite', db: 'ai_platform' },
    { role: 'dbAdmin', db: 'ai_platform' }
  ]
});

// 创建系统日志集合
db.createCollection('system_logs');
db.system_logs.createIndex({ "timestamp": 1 });
db.system_logs.createIndex({ "level": 1, "timestamp": 1 });
db.system_logs.createIndex({ "service": 1, "timestamp": 1 });

// 创建配置集合
db.createCollection('configurations');
db.configurations.createIndex({ "component": 1, "environment": 1, "version": 1 });
db.configurations.createIndex({ "is_active": 1 });

// 创建任务状态缓存集合
db.createCollection('task_status_cache');
db.task_status_cache.createIndex({ "task_id": 1 });
db.task_status_cache.createIndex({ "status": 1, "last_updated": 1 });
db.task_status_cache.createIndex({ "task_type": 1, "status": 1 });
db.task_status_cache.createIndex({ "last_updated": 1 }, { expireAfterSeconds: 86400 });

print('MongoDB初始化完成');
