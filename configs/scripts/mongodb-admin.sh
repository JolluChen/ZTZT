#!/bin/bash

MONGO_CONTAINER="mongodb"
MONGO_USER="ai_platform_user"
MONGO_PASS="changeThisToSecurePassword"
MONGO_DB="ai_platform"

case "$1" in
    "status")
        echo "=== MongoDB 容器状态 ==="
        docker compose -f docker-compose-mongodb.yml ps
        echo ""
        echo "=== 资源使用情况 ==="
        docker stats ${MONGO_CONTAINER} --no-stream
        ;;
    "logs")
        echo "=== MongoDB 日志 ==="
        docker compose -f docker-compose-mongodb.yml logs -f ${MONGO_CONTAINER}
        ;;
    "shell")
        echo "连接到 MongoDB shell..."
        docker exec -it ${MONGO_CONTAINER} mongosh -u ${MONGO_USER} -p ${MONGO_PASS} --authenticationDatabase ${MONGO_DB} ${MONGO_DB}
        ;;
    "backup")
        BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p ${BACKUP_DIR}
        echo "备份数据库到: ${BACKUP_DIR}"
        docker exec ${MONGO_CONTAINER} mongodump --host localhost --port 27017 \
            -u ${MONGO_USER} -p ${MONGO_PASS} --authenticationDatabase ${MONGO_DB} \
            --db ${MONGO_DB} --out /tmp/backup
        docker cp ${MONGO_CONTAINER}:/tmp/backup/${MONGO_DB} ${BACKUP_DIR}/
        echo "备份完成: ${BACKUP_DIR}"
        ;;
    "restore")
        if [ -z "$2" ]; then
            echo "请指定备份目录路径"
            echo "用法: $0 restore <backup_directory>"
            exit 1
        fi
        echo "从 $2 恢复数据库..."
        docker cp "$2" ${MONGO_CONTAINER}:/tmp/restore
        docker exec ${MONGO_CONTAINER} mongorestore --host localhost --port 27017 \
            -u ${MONGO_USER} -p ${MONGO_PASS} --authenticationDatabase ${MONGO_DB} \
            --db ${MONGO_DB} --drop /tmp/restore
        echo "恢复完成"
        ;;
    "stats")
        echo "=== 数据库统计信息 ==="
        docker exec -it ${MONGO_CONTAINER} mongosh -u ${MONGO_USER} -p ${MONGO_PASS} \
            --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "
            print('=== 数据库统计 ===');
            printjson(db.stats());
            print('\\n=== 各集合文档数量 ===');
            db.runCommand('listCollections').cursor.firstBatch.forEach(function(collection) {
                var count = db[collection.name].countDocuments();
                print(collection.name + ': ' + count + ' 个文档');
            });
            print('\\n=== 索引统计 ===');
            db.runCommand('listCollections').cursor.firstBatch.forEach(function(collection) {
                var indexes = db[collection.name].getIndexes();
                print(collection.name + ': ' + indexes.length + ' 个索引');
            });
        "
        ;;
    "monitor")
        echo "=== 数据库性能监控 ==="
        docker exec -it ${MONGO_CONTAINER} mongosh -u ${MONGO_USER} -p ${MONGO_PASS} \
            --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "
            print('=== 数据库状态 ===');
            let dbStats = db.stats();
            print('数据库名称:', db.getName());
            print('数据库大小:', Math.round(dbStats.dataSize / 1024 / 1024), 'MB');
            print('索引大小:', Math.round(dbStats.indexSize / 1024 / 1024), 'MB');
            print('集合数量:', dbStats.collections);
            print('文档总数:', dbStats.objects);
            
            print('\\n=== 服务器状态 ===');
            let serverStatus = db.runCommand('serverStatus');
            print('MongoDB 版本:', serverStatus.version);
            print('运行时间:', Math.round(serverStatus.uptime / 3600), '小时');
            print('当前连接数:', serverStatus.connections.current);
            print('可用连接数:', serverStatus.connections.available);
            
            print('\\n=== 内存使用情况 ===');
            if (serverStatus.wiredTiger) {
                let cache = serverStatus.wiredTiger.cache;
                print('缓存大小上限:', Math.round(cache['maximum bytes configured'] / 1024 / 1024), 'MB');
                print('当前缓存使用:', Math.round(cache['bytes currently in the cache'] / 1024 / 1024), 'MB');
                print('缓存命中率:', Math.round(cache['unmodified pages evicted'] * 100 / (cache['unmodified pages evicted'] + cache['pages read into cache'])), '%');
            }
            
            print('\\n=== 各集合详细统计 ===');
            ['system_logs', 'configurations', 'task_status_cache'].forEach(function(collName) {
                try {
                    let collStats = db[collName].stats();
                    print('--- ' + collName + ' ---');
                    print('  文档数量:', collStats.count);
                    print('  数据大小:', Math.round(collStats.size / 1024), 'KB');
                    print('  索引数量:', collStats.nindexes);
                    print('  索引大小:', Math.round(collStats.totalIndexSize / 1024), 'KB');
                } catch (e) {
                    print('集合', collName, '统计获取失败:', e.message);
                }
            });
        "
        ;;
    "indexes")
        echo "=== 索引信息 ==="
        docker exec -it ${MONGO_CONTAINER} mongosh -u ${MONGO_USER} -p ${MONGO_PASS} \
            --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "
            ['system_logs', 'configurations', 'task_status_cache'].forEach(function(collName) {
                print('\\n=== ' + collName + ' 索引 ===');
                try {
                    db[collName].getIndexes().forEach(function(index) {
                        print('索引名: ' + index.name);
                        print('键: ' + JSON.stringify(index.key));
                        if (index.unique) print('唯一索引: 是');
                        if (index.expireAfterSeconds) print('TTL: ' + index.expireAfterSeconds + ' 秒');
                        print('---');
                    });
                } catch (e) {
                    print('获取', collName, '索引失败:', e.message);
                }
            });
        "
        ;;
    "query-test")
        echo "=== 查询性能测试 ==="
        docker exec -it ${MONGO_CONTAINER} mongosh -u ${MONGO_USER} -p ${MONGO_PASS} \
            --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "
            print('=== 时间范围查询测试 ===');
            var startTime = new Date(Date.now() - 3600000);
            var start = new Date();
            var result = db.system_logs.find({timestamp: {\$gte: startTime}}).count();
            var end = new Date();
            print('查询结果: ' + result + ' 条记录');
            print('查询耗时: ' + (end - start) + ' 毫秒');
            
            print('\\n=== 复合查询测试 ===');
            var start = new Date();
            var result = db.system_logs.find({level: 'INFO', timestamp: {\$gte: startTime}}).count();
            var end = new Date();
            print('查询结果: ' + result + ' 条记录');
            print('查询耗时: ' + (end - start) + ' 毫秒');
            
            print('\\n=== 任务状态查询测试 ===');
            var start = new Date();
            var result = db.task_status_cache.find({status: 'COMPLETED'}).count();
            var end = new Date();
            print('已完成任务: ' + result + ' 个');
            print('查询耗时: ' + (end - start) + ' 毫秒');
            
            print('\\n=== 索引使用分析 ===');
            var plan = db.system_logs.find({level: 'INFO'}).explain('executionStats');
            print('INFO日志查询执行阶段:', plan.executionStats.executionStages.stage);
            if (plan.executionStats.executionStages.indexName) {
                print('使用索引:', plan.executionStats.executionStages.indexName);
            } else if (plan.executionStats.executionStages.inputStage && plan.executionStats.executionStages.inputStage.indexName) {
                print('使用索引:', plan.executionStats.executionStages.inputStage.indexName);
            } else {
                print('使用索引: 无 (全表扫描)');
            }
        "
        ;;
    "data-sample")
        echo "=== 查看样本数据 ==="
        docker exec -it ${MONGO_CONTAINER} mongosh -u ${MONGO_USER} -p ${MONGO_PASS} \
            --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "
            print('=== 最近的系统日志 (前5条) ===');
            db.system_logs.find().sort({timestamp: -1}).limit(5).forEach(function(doc) {
                print('时间: ' + doc.timestamp + ', 级别: ' + doc.level + ', 服务: ' + doc.service);
                print('消息: ' + doc.message);
                print('---');
            });
            
            print('\\n=== 活跃配置 ===');
            db.configurations.find({is_active: true}).forEach(function(doc) {
                print('组件: ' + doc.component + ', 环境: ' + doc.environment + ', 版本: ' + doc.version);
            });
            
            print('\\n=== 任务状态分布 ===');
            var statusCounts = {};
            db.task_status_cache.find().forEach(function(doc) {
                statusCounts[doc.status] = (statusCounts[doc.status] || 0) + 1;
            });
            for (var status in statusCounts) {
                print(status + ': ' + statusCounts[status] + ' 个任务');
            }
        "
        ;;
    "health-check")
        echo "=== MongoDB 健康检查 $(date) ==="
        
        # 检查容器状态
        if docker ps | grep -q ${MONGO_CONTAINER}; then
            echo "✅ MongoDB 容器运行正常"
        else
            echo "❌ MongoDB 容器未运行"
            exit 1
        fi
        
        # 检查数据库连接
        if docker exec ${MONGO_CONTAINER} mongosh --quiet -u ${MONGO_USER} -p ${MONGO_PASS} --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "db.runCommand('ping')" > /dev/null 2>&1; then
            echo "✅ 数据库连接正常"
        else
            echo "❌ 数据库连接失败"
            exit 1
        fi
        
        # 检查磁盘空间
        DISK_USAGE=$(docker exec ${MONGO_CONTAINER} df /data/db | tail -1 | awk '{print $5}' | sed 's/%//')
        if [ "$DISK_USAGE" -lt 80 ]; then
            echo "✅ 磁盘空间充足 (${DISK_USAGE}% 使用)"
        else
            echo "⚠️  磁盘空间不足 (${DISK_USAGE}% 使用)"
        fi
        
        # 检查集合数量
        COLLECTIONS=$(docker exec ${MONGO_CONTAINER} mongosh --quiet -u ${MONGO_USER} -p ${MONGO_PASS} --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "db.runCommand('listCollections').cursor.firstBatch.length")
        if [ "$COLLECTIONS" -ge 3 ]; then
            echo "✅ 集合创建正常 ($COLLECTIONS 个集合)"
        else
            echo "⚠️  集合数量异常 ($COLLECTIONS 个集合)"
        fi
        
        # 检查索引数量
        INDEX_TOTAL=$(docker exec ${MONGO_CONTAINER} mongosh --quiet -u ${MONGO_USER} -p ${MONGO_PASS} --authenticationDatabase ${MONGO_DB} ${MONGO_DB} --eval "
            let total = 0;
            ['system_logs', 'configurations', 'task_status_cache'].forEach(function(coll) {
                try {
                    total += db[coll].getIndexes().length;
                } catch(e) {}
            });
            print(total);
        ")
        if [ "$INDEX_TOTAL" -ge 10 ]; then
            echo "✅ 索引创建正常 ($INDEX_TOTAL 个索引)"
        else
            echo "⚠️  索引数量异常 ($INDEX_TOTAL 个索引)"
        fi
        
        echo "=== 健康检查完成 ==="
        ;;
    "restart")
        echo "重启 MongoDB 服务..."
        docker compose -f docker-compose-mongodb.yml restart ${MONGO_CONTAINER}
        sleep 10
        docker compose -f docker-compose-mongodb.yml ps
        ;;
    *)
        echo "MongoDB 管理脚本使用说明:"
        echo "  $0 status           - 查看服务状态"
        echo "  $0 logs             - 查看日志"
        echo "  $0 shell            - 连接到 MongoDB shell"
        echo "  $0 backup           - 备份数据库"
        echo "  $0 restore <dir>    - 从备份恢复数据库"
        echo "  $0 stats            - 查看数据库统计"
        echo "  $0 monitor          - 性能监控"
        echo "  $0 indexes          - 查看索引信息"
        echo "  $0 query-test       - 运行查询性能测试"
        echo "  $0 data-sample      - 查看样本数据"
        echo "  $0 health-check     - 运行健康检查"
        echo "  $0 restart          - 重启服务"
        ;;
esac
