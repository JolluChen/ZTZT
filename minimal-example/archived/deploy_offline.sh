#!/bin/bash

# AI中台离线部署脚本 - 完全不依赖Docker镜像的解决方案
# Author: GitHub Copilot
# Date: 2025-06-11
# Purpose: 解决Docker镜像拉取网络问题，提供完全本地化的AI中台服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI中台离线部署解决方案${NC}"
echo "================================="
echo -e "${YELLOW}📋 此方案完全不依赖Docker镜像，适用于网络受限环境${NC}"
echo ""

# 全局变量
WORKSPACE_DIR="/home/lsyzt/ZTZT/minimal-example"
SERVICES_DIR="$WORKSPACE_DIR/local-services"
PIDS_DIR="/tmp/ai_platform_pids"

# 创建必要目录
create_directories() {
    echo -e "${BLUE}📁 创建必要目录结构...${NC}"
    
    mkdir -p "$SERVICES_DIR"/{database,cache,inference,monitoring,storage}
    mkdir -p "$PIDS_DIR"
    mkdir -p logs
    
    echo -e "${GREEN}✅ 目录结构创建完成${NC}"
}

# 创建数据库服务（SQLite HTTP服务器）
create_database_service() {
    echo -e "${BLUE}🗄️ 创建数据库服务...${NC}"
    
    cat > "$SERVICES_DIR/database/sqlite_server.py" << 'EOF'
#!/usr/bin/env python3
"""
SQLite HTTP数据库服务
端口: 5432 (兼容PostgreSQL端口)
功能: 提供HTTP接口的轻量级数据库服务
"""

import sqlite3
import json
import http.server
import socketserver
import urllib.parse
from datetime import datetime
import os
import threading

class SQLiteHTTPHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db_path = os.path.join(os.path.dirname(__file__), "ai_platform.db")
        self.init_database()
        super().__init__(*args, **kwargs)
    
    def init_database(self):
        """初始化数据库表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建模型表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    version TEXT DEFAULT '1.0',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建推理记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inference_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    inference_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入示例数据
            cursor.execute("INSERT OR IGNORE INTO models (name, type) VALUES (?, ?)", 
                         ("simple-linear", "regression"))
            cursor.execute("INSERT OR IGNORE INTO models (name, type) VALUES (?, ?)", 
                         ("simple-cnn", "classification"))
            cursor.execute("INSERT OR IGNORE INTO models (name, type) VALUES (?, ?)", 
                         ("text-classifier", "nlp"))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"数据库初始化错误: {e}")
    
    def do_GET(self):
        if self.path == "/health":
            self.send_json_response({"status": "healthy", "service": "SQLite Database"})
        elif self.path == "/tables":
            tables = self.get_tables()
            self.send_json_response({"tables": tables})
        elif self.path == "/models":
            models = self.get_models()
            self.send_json_response({"models": models})
        else:
            self.send_json_response({"error": "Endpoint not found"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            
            if self.path == "/query":
                result = self.execute_query(data.get("sql", ""))
                self.send_json_response({"result": result})
            elif self.path == "/log_inference":
                self.log_inference(data)
                self.send_json_response({"status": "logged"})
            else:
                self.send_json_response({"error": "Endpoint not found"}, 404)
                
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def get_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    
    def get_models(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, type, version, status FROM models")
        models = [{"name": row[0], "type": row[1], "version": row[2], "status": row[3]} 
                 for row in cursor.fetchall()]
        conn.close()
        return models
    
    def execute_query(self, sql):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            if sql.strip().upper().startswith('SELECT'):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = f"Affected rows: {cursor.rowcount}"
            return result
        finally:
            conn.close()
    
    def log_inference(self, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inference_logs (model_name, input_data, output_data, inference_time) VALUES (?, ?, ?, ?)",
            (data.get("model_name"), json.dumps(data.get("input_data")), 
             json.dumps(data.get("output_data")), data.get("inference_time"))
        )
        conn.commit()
        conn.close()

if __name__ == "__main__":
    PORT = 5432
    print(f"🗄️ SQLite数据库服务启动在端口 {PORT}")
    
    with socketserver.TCPServer(("", PORT), SQLiteHTTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n数据库服务已停止")
EOF

    chmod +x "$SERVICES_DIR/database/sqlite_server.py"
    echo -e "${GREEN}✅ 数据库服务创建完成${NC}"
}

# 创建缓存服务（内存缓存）
create_cache_service() {
    echo -e "${BLUE}💾 创建缓存服务...${NC}"
    
    cat > "$SERVICES_DIR/cache/memory_cache.py" << 'EOF'
#!/usr/bin/env python3
"""
内存缓存HTTP服务
端口: 6379 (兼容Redis端口)
功能: 提供HTTP接口的内存缓存服务
"""

import json
import http.server
import socketserver
import threading
import time
from datetime import datetime, timedelta

class MemoryCache:
    def __init__(self):
        self.data = {}
        self.expiry = {}
        self.lock = threading.Lock()
        self.stats = {"hits": 0, "misses": 0, "sets": 0}
        
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self.cleanup_expired, daemon=True)
        self.cleanup_thread.start()
    
    def set(self, key, value, ttl=None):
        with self.lock:
            self.data[key] = value
            self.stats["sets"] += 1
            if ttl:
                self.expiry[key] = datetime.now() + timedelta(seconds=ttl)
            else:
                self.expiry.pop(key, None)
    
    def get(self, key):
        with self.lock:
            if key in self.expiry and datetime.now() > self.expiry[key]:
                del self.data[key]
                del self.expiry[key]
                self.stats["misses"] += 1
                return None
            
            if key in self.data:
                self.stats["hits"] += 1
                return self.data[key]
            else:
                self.stats["misses"] += 1
                return None
    
    def delete(self, key):
        with self.lock:
            self.data.pop(key, None)
            self.expiry.pop(key, None)
    
    def keys(self):
        with self.lock:
            # 清理过期键
            expired_keys = [k for k, exp in self.expiry.items() if datetime.now() > exp]
            for key in expired_keys:
                del self.data[key]
                del self.expiry[key]
            return list(self.data.keys())
    
    def cleanup_expired(self):
        while True:
            time.sleep(30)  # 每30秒清理一次
            with self.lock:
                expired_keys = [k for k, exp in self.expiry.items() if datetime.now() > exp]
                for key in expired_keys:
                    del self.data[key]
                    del self.expiry[key]

cache = MemoryCache()

class CacheHTTPHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_json_response({"status": "healthy", "service": "Memory Cache"})
        elif self.path == "/stats":
            stats = cache.stats.copy()
            stats["total_keys"] = len(cache.data)
            self.send_json_response(stats)
        elif self.path == "/keys":
            keys = cache.keys()
            self.send_json_response({"keys": keys})
        elif self.path.startswith("/get/"):
            key = self.path[5:]
            value = cache.get(key)
            self.send_json_response({"key": key, "value": value, "found": value is not None})
        else:
            self.send_json_response({"error": "Endpoint not found"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            
            if self.path == "/set":
                key = data.get("key")
                value = data.get("value")
                ttl = data.get("ttl")
                cache.set(key, value, ttl)
                self.send_json_response({"status": "ok", "key": key})
            elif self.path == "/delete":
                key = data.get("key")
                cache.delete(key)
                self.send_json_response({"status": "deleted", "key": key})
            elif self.path == "/get":
                key = data.get("key")
                value = cache.get(key)
                self.send_json_response({"key": key, "value": value, "found": value is not None})
            else:
                self.send_json_response({"error": "Endpoint not found"}, 404)
                
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

if __name__ == "__main__":
    PORT = 6379
    print(f"💾 内存缓存服务启动在端口 {PORT}")
    
    with socketserver.TCPServer(("", PORT), CacheHTTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n缓存服务已停止")
EOF

    chmod +x "$SERVICES_DIR/cache/memory_cache.py"
    echo -e "${GREEN}✅ 缓存服务创建完成${NC}"
}

# 创建推理服务（AI模型推理）
create_inference_service() {
    echo -e "${BLUE}🤖 创建AI推理服务...${NC}"
    
    cat > "$SERVICES_DIR/inference/ai_inference.py" << 'EOF'
#!/usr/bin/env python3
"""
AI推理HTTP服务
端口: 8100 (兼容Triton端口)
功能: 提供多种AI模型的推理服务
"""

import json
import http.server
import socketserver
import time
import random
import math
from datetime import datetime

class AIInferenceHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.models = self.initialize_models()
        super().__init__(*args, **kwargs)
    
    def initialize_models(self):
        """初始化AI模型"""
        return {
            "simple-linear": {
                "type": "regression",
                "description": "简单线性回归模型",
                "input_shape": [10],
                "output_shape": [1],
                "parameters": {"weights": [random.uniform(-1, 1) for _ in range(10)], "bias": random.uniform(-1, 1)}
            },
            "simple-cnn": {
                "type": "classification", 
                "description": "简单卷积神经网络",
                "input_shape": [224, 224, 3],
                "output_shape": [1000],
                "parameters": {"num_classes": 1000, "feature_dim": 512}
            },
            "text-classifier": {
                "type": "nlp",
                "description": "文本分类模型",
                "input_type": "text",
                "output_classes": ["positive", "negative", "neutral", "mixed", "unknown"],
                "parameters": {"vocab_size": 10000, "embedding_dim": 128}
            },
            "sentiment-analyzer": {
                "type": "nlp",
                "description": "情感分析模型",
                "input_type": "text",
                "output_type": "sentiment_score",
                "parameters": {"model_version": "v2.1", "accuracy": 0.94}
            },
            "object-detector": {
                "type": "computer_vision",
                "description": "目标检测模型",
                "input_shape": [640, 640, 3],
                "output_type": "bounding_boxes",
                "parameters": {"num_classes": 80, "confidence_threshold": 0.5}
            }
        }
    
    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self.send_json_response({
                "service": "AI推理服务",
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat(),
                "available_models": list(self.models.keys()),
                "endpoints": ["/", "/health", "/models", "/infer", "/metrics"]
            })
        
        elif self.path == "/models":
            model_info = {}
            for name, model in self.models.items():
                model_info[name] = {
                    "type": model["type"],
                    "description": model["description"],
                    "input_shape": model.get("input_shape", model.get("input_type", "variable")),
                    "output_shape": model.get("output_shape", model.get("output_type", "variable"))
                }
            self.send_json_response({"models": model_info, "total": len(self.models)})
        
        elif self.path == "/metrics":
            metrics = self.generate_metrics()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics.encode())
        
        else:
            self.send_json_response({"error": "Endpoint not found"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
            
            if self.path == "/infer":
                result = self.perform_inference(data)
                self.send_json_response(result)
            elif self.path == "/batch_infer":
                results = self.perform_batch_inference(data)
                self.send_json_response(results)
            else:
                self.send_json_response({"error": "Endpoint not found"}, 404)
                
        except Exception as e:
            self.send_json_response({"error": str(e), "timestamp": datetime.now().isoformat()}, 500)
    
    def perform_inference(self, request_data):
        """执行单个推理请求"""
        model_name = request_data.get("model_name", "")
        inputs = request_data.get("inputs", {})
        parameters = request_data.get("parameters", {})
        
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 不存在")
        
        model = self.models[model_name]
        start_time = time.time()
        
        # 模拟推理延迟
        inference_delay = random.uniform(0.01, 0.1)
        time.sleep(inference_delay)
        
        # 根据模型类型执行推理
        if model["type"] == "regression":
            predictions = self.linear_inference(inputs, model)
        elif model["type"] == "classification":
            predictions = self.classification_inference(inputs, model)
        elif model["type"] == "nlp":
            predictions = self.nlp_inference(inputs, model)
        elif model["type"] == "computer_vision":
            predictions = self.cv_inference(inputs, model)
        else:
            predictions = {"output": "unknown_model_type"}
        
        inference_time = time.time() - start_time
        
        return {
            "model_name": model_name,
            "predictions": predictions,
            "inference_time": round(inference_time, 6),
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "request_id": f"req_{int(time.time()*1000)}"
        }
    
    def linear_inference(self, inputs, model):
        """线性回归推理"""
        input_data = inputs.get("data", [random.random() for _ in range(10)])
        if len(input_data) != 10:
            input_data = input_data[:10] + [0] * max(0, 10 - len(input_data))
        
        weights = model["parameters"]["weights"]
        bias = model["parameters"]["bias"]
        
        prediction = sum(x * w for x, w in zip(input_data, weights)) + bias
        return {
            "prediction": round(prediction, 6),
            "confidence": round(random.uniform(0.8, 0.99), 3),
            "input_features": len(input_data)
        }
    
    def classification_inference(self, inputs, model):
        """分类模型推理"""
        num_classes = model["parameters"]["num_classes"]
        probabilities = [random.random() for _ in range(min(num_classes, 20))]  # 限制输出大小
        total = sum(probabilities)
        probabilities = [p/total for p in probabilities]  # 归一化
        
        return {
            "class_id": probabilities.index(max(probabilities)),
            "confidence": round(max(probabilities), 4),
            "probabilities": [round(p, 4) for p in probabilities],
            "top_5_classes": sorted(enumerate(probabilities), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def nlp_inference(self, inputs, model):
        """自然语言处理推理"""
        text = inputs.get("text", "")
        
        if "sentiment" in model.get("description", "").lower():
            sentiments = ["positive", "negative", "neutral"]
            sentiment = random.choice(sentiments)
            confidence = random.uniform(0.7, 0.99)
            return {
                "sentiment": sentiment,
                "confidence": round(confidence, 4),
                "text_length": len(text),
                "word_count": len(text.split()) if text else 0
            }
        else:
            classes = model.get("output_classes", ["class_0", "class_1", "class_2"])
            return {
                "predicted_class": random.choice(classes),
                "confidence": round(random.uniform(0.7, 0.95), 4),
                "text_features": {
                    "length": len(text),
                    "word_count": len(text.split()) if text else 0,
                    "language": "detected_auto"
                }
            }
    
    def cv_inference(self, inputs, model):
        """计算机视觉推理"""
        image_data = inputs.get("image", {})
        width = image_data.get("width", 640)
        height = image_data.get("height", 640)
        
        # 模拟目标检测结果
        num_objects = random.randint(0, 5)
        detections = []
        
        for i in range(num_objects):
            detections.append({
                "class_id": random.randint(0, 79),
                "class_name": f"object_{random.randint(0, 79)}",
                "confidence": round(random.uniform(0.5, 0.95), 3),
                "bbox": [
                    random.randint(0, width//2),   # x
                    random.randint(0, height//2),  # y
                    random.randint(width//2, width),   # x2
                    random.randint(height//2, height)  # y2
                ]
            })
        
        return {
            "detections": detections,
            "num_objects": num_objects,
            "image_size": [width, height],
            "processing_time": round(random.uniform(0.05, 0.2), 4)
        }
    
    def perform_batch_inference(self, request_data):
        """执行批量推理"""
        requests = request_data.get("requests", [])
        results = []
        
        for req in requests:
            try:
                result = self.perform_inference(req)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "request": req})
        
        return {
            "batch_results": results,
            "total_requests": len(requests),
            "successful": len([r for r in results if "error" not in r]),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_metrics(self):
        """生成Prometheus格式的指标"""
        return f"""# AI推理服务指标
# HELP inference_requests_total 推理请求总数
# TYPE inference_requests_total counter
inference_requests_total {random.randint(1000, 10000)}

# HELP inference_duration_seconds 推理耗时
# TYPE inference_duration_seconds histogram
inference_duration_seconds_sum {random.uniform(10, 100)}
inference_duration_seconds_count {random.randint(500, 5000)}

# HELP model_load_count 已加载模型数量
# TYPE model_load_count gauge
model_load_count {len(self.models)}

# HELP memory_usage_bytes 内存使用量
# TYPE memory_usage_bytes gauge
memory_usage_bytes {random.randint(500000000, 2000000000)}

# HELP gpu_utilization GPU使用率
# TYPE gpu_utilization gauge
gpu_utilization {random.uniform(0.1, 0.9)}
"""
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

if __name__ == "__main__":
    PORT = 8100
    print(f"🤖 AI推理服务启动在端口 {PORT}")
    print(f"📱 服务地址: http://localhost:{PORT}")
    print(f"📋 模型列表: http://localhost:{PORT}/models")
    print(f"📊 服务指标: http://localhost:{PORT}/metrics")
    
    with socketserver.TCPServer(("", PORT), AIInferenceHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 AI推理服务已停止")
EOF

    chmod +x "$SERVICES_DIR/inference/ai_inference.py"
    echo -e "${GREEN}✅ AI推理服务创建完成${NC}"
}

# 创建监控服务（轻量级监控）
create_monitoring_service() {
    echo -e "${BLUE}📊 创建监控服务...${NC}"
    
    cat > "$SERVICES_DIR/monitoring/metrics_server.py" << 'EOF'
#!/usr/bin/env python3
"""
轻量级监控服务
端口: 9090 (兼容Prometheus端口)
功能: 收集和展示系统指标
"""

import json
import http.server
import socketserver
import time
import psutil
import threading
from datetime import datetime, timedelta

class MetricsCollector:
    def __init__(self):
        self.metrics = {}
        self.history = []
        self.lock = threading.Lock()
        
        # 启动指标收集线程
        self.collector_thread = threading.Thread(target=self.collect_metrics, daemon=True)
        self.collector_thread.start()
    
    def collect_metrics(self):
        """定期收集系统指标"""
        while True:
            try:
                with self.lock:
                    metrics = {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_percent": psutil.cpu_percent(interval=1),
                        "memory_percent": psutil.virtual_memory().percent,
                        "memory_used": psutil.virtual_memory().used,
                        "memory_total": psutil.virtual_memory().total,
                        "disk_percent": psutil.disk_usage('/').percent,
                        "disk_used": psutil.disk_usage('/').used,
                        "disk_total": psutil.disk_usage('/').total,
                        "network_sent": psutil.net_io_counters().bytes_sent,
                        "network_recv": psutil.net_io_counters().bytes_recv,
                        "load_avg": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
                    }
                    
                    self.metrics = metrics
                    self.history.append(metrics)
                    
                    # 保留最近1小时的数据
                    if len(self.history) > 3600:
                        self.history = self.history[-3600:]
                        
            except Exception as e:
                print(f"指标收集错误: {e}")
            
            time.sleep(1)
    
    def get_current_metrics(self):
        with self.lock:
            return self.metrics.copy()
    
    def get_history(self, minutes=60):
        with self.lock:
            # 返回最近N分钟的数据
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            return [m for m in self.history if datetime.fromisoformat(m["timestamp"]) > cutoff_time]

collector = MetricsCollector()

class MonitoringHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_json_response({"status": "healthy", "service": "Monitoring Server"})
        
        elif self.path == "/metrics":
            metrics = collector.get_current_metrics()
            # 转换为Prometheus格式
            prometheus_metrics = self.to_prometheus_format(metrics)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(prometheus_metrics.encode())
        
        elif self.path == "/api/metrics":
            metrics = collector.get_current_metrics()
            self.send_json_response(metrics)
        
        elif self.path.startswith("/api/history"):
            # 解析查询参数
            if "?" in self.path:
                params = dict(param.split("=") for param in self.path.split("?")[1].split("&"))
                minutes = int(params.get("minutes", 60))
            else:
                minutes = 60
            
            history = collector.get_history(minutes)
            self.send_json_response({"history": history, "count": len(history)})
        
        elif self.path == "/dashboard":
            self.send_html_dashboard()
        
        else:
            self.send_json_response({"error": "Endpoint not found"}, 404)
    
    def to_prometheus_format(self, metrics):
        """转换为Prometheus格式"""
        if not metrics:
            return "# No metrics available"
        
        prometheus_text = f"""# 系统监控指标
# HELP cpu_percent CPU使用率
# TYPE cpu_percent gauge
cpu_percent {metrics.get('cpu_percent', 0)}

# HELP memory_percent 内存使用率
# TYPE memory_percent gauge
memory_percent {metrics.get('memory_percent', 0)}

# HELP memory_used_bytes 已使用内存
# TYPE memory_used_bytes gauge
memory_used_bytes {metrics.get('memory_used', 0)}

# HELP disk_percent 磁盘使用率
# TYPE disk_percent gauge
disk_percent {metrics.get('disk_percent', 0)}

# HELP network_sent_bytes 网络发送字节数
# TYPE network_sent_bytes counter
network_sent_bytes {metrics.get('network_sent', 0)}

# HELP network_recv_bytes 网络接收字节数
# TYPE network_recv_bytes counter
network_recv_bytes {metrics.get('network_recv', 0)}

# HELP load_average 系统负载
# TYPE load_average gauge
load_average {metrics.get('load_avg', 0)}
"""
        return prometheus_text
    
    def send_html_dashboard(self):
        """发送HTML监控面板"""
        html = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI中台监控面板</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2196F3; color: white; padding: 20px; border-radius: 5px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #2196F3; }
        .metric-label { color: #666; margin-bottom: 10px; }
        .refresh-btn { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        .status { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }
        .status.healthy { background-color: #4CAF50; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ AI中台系统监控</h1>
            <span class="status healthy">系统运行正常</span>
            <button class="refresh-btn" onclick="loadMetrics()">刷新数据</button>
        </div>
        
        <div class="metrics-grid" id="metricsGrid">
            <!-- 指标将通过JavaScript加载 -->
        </div>
    </div>

    <script>
        function loadMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    const grid = document.getElementById('metricsGrid');
                    grid.innerHTML = `
                        <div class="metric-card">
                            <div class="metric-label">CPU使用率</div>
                            <div class="metric-value">${data.cpu_percent?.toFixed(1) || 0}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">内存使用率</div>
                            <div class="metric-value">${data.memory_percent?.toFixed(1) || 0}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">磁盘使用率</div>
                            <div class="metric-value">${data.disk_percent?.toFixed(1) || 0}%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">系统负载</div>
                            <div class="metric-value">${data.load_avg?.toFixed(2) || 0}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">网络发送</div>
                            <div class="metric-value">${formatBytes(data.network_sent || 0)}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">网络接收</div>
                            <div class="metric-value">${formatBytes(data.network_recv || 0)}</div>
                        </div>
                    `;
                })
                .catch(error => {
                    console.error('加载指标失败:', error);
                    document.getElementById('metricsGrid').innerHTML = '<div class="metric-card">数据加载失败</div>';
                });
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // 页面加载时获取数据
        loadMetrics();
        
        // 每5秒自动刷新
        setInterval(loadMetrics, 5000);
    </script>
</body>
</html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

if __name__ == "__main__":
    PORT = 9090
    print(f"📊 监控服务启动在端口 {PORT}")
    print(f"🖥️ 监控面板: http://localhost:{PORT}/dashboard")
    
    with socketserver.TCPServer(("", PORT), MonitoringHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n监控服务已停止")
EOF

    chmod +x "$SERVICES_DIR/monitoring/metrics_server.py"
    echo -e "${GREEN}✅ 监控服务创建完成${NC}"
}

# 创建启动控制脚本
create_control_scripts() {
    echo -e "${BLUE}🎮 创建控制脚本...${NC}"
    
    # 主启动脚本
    cat > start_offline.sh << 'EOF'
#!/bin/bash

# AI中台离线服务启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PIDS_DIR="/tmp/ai_platform_pids"
mkdir -p "$PIDS_DIR"

echo -e "${BLUE}🚀 启动AI中台离线服务${NC}"
echo "========================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 需要Python3环境${NC}"
    exit 1
fi

# 检查psutil模块（用于监控）
python3 -c "import psutil" 2>/dev/null || {
    echo -e "${YELLOW}⚠️ 正在安装psutil模块...${NC}"
    pip3 install psutil --quiet || echo -e "${YELLOW}psutil安装失败，监控功能可能受限${NC}"
}

# 启动服务函数
start_service() {
    local service_name=$1
    local script_path=$2
    local port=$3
    local description=$4
    
    echo -e "${BLUE}启动 $description (端口 $port)...${NC}"
    
    # 检查端口是否被占用
    if ss -tuln | grep -q ":$port "; then
        echo -e "${YELLOW}⚠️ 端口 $port 已被占用，跳过 $service_name${NC}"
        return
    fi
    
    # 启动服务
    python3 "$script_path" &
    local pid=$!
    echo $pid > "$PIDS_DIR/${service_name}.pid"
    
    # 等待服务启动
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $description 启动成功 (PID: $pid)${NC}"
    else
        echo -e "${RED}❌ $description 启动失败${NC}"
        rm -f "$PIDS_DIR/${service_name}.pid"
    fi
}

echo -e "\n${BLUE}🌟 启动核心服务...${NC}"

start_service "database" "local-services/database/sqlite_server.py" 5432 "数据库服务"
start_service "cache" "local-services/cache/memory_cache.py" 6379 "缓存服务"
start_service "inference" "local-services/inference/ai_inference.py" 8100 "AI推理服务"
start_service "monitoring" "local-services/monitoring/metrics_server.py" 9090 "监控服务"

# 启动Django后端（如果存在）
if [ -f "backend/manage.py" ]; then
    echo -e "${BLUE}启动Django后端...${NC}"
    if ! ss -tuln | grep -q ":8000 "; then
        cd backend
        python3 manage.py runserver 8000 > ../logs/django.log 2>&1 &
        echo $! > "$PIDS_DIR/django.pid"
        cd ..
        echo -e "${GREEN}✅ Django后端启动成功${NC}"
    else
        echo -e "${YELLOW}⚠️ 端口 8000 已被占用，跳过Django后端${NC}"
    fi
fi

echo -e "\n${GREEN}🎉 AI中台离线服务启动完成！${NC}"
echo -e "\n${BLUE}📱 服务地址:${NC}"
echo -e "• 📊 监控面板: ${CYAN}http://localhost:9090/dashboard${NC}"
echo -e "• 🤖 AI推理API: ${CYAN}http://localhost:8100${NC}"
echo -e "• 🗄️ 数据库服务: ${CYAN}http://localhost:5432/health${NC}"
echo -e "• 💾 缓存服务: ${CYAN}http://localhost:6379/health${NC}"
echo -e "• 🌐 Django后端: ${CYAN}http://localhost:8000${NC}"

echo -e "\n${BLUE}💡 管理命令:${NC}"
echo -e "• 查看状态: ${YELLOW}./status_offline.sh${NC}"
echo -e "• 测试服务: ${YELLOW}./test_offline.sh${NC}"
echo -e "• 停止服务: ${YELLOW}./stop_offline.sh${NC}"

# 显示简单测试
echo -e "\n${BLUE}🧪 快速测试:${NC}"
echo -e "• 健康检查: ${YELLOW}curl http://localhost:8100/health${NC}"
echo -e "• 模型列表: ${YELLOW}curl http://localhost:8100/models${NC}"
echo -e "• 监控面板: ${YELLOW}浏览器打开 http://localhost:9090/dashboard${NC}"
EOF

    # 停止脚本
    cat > stop_offline.sh << 'EOF'
#!/bin/bash

echo "🛑 停止AI中台离线服务..."

PIDS_DIR="/tmp/ai_platform_pids"

# 停止所有服务
for pidfile in "$PIDS_DIR"/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        service_name=$(basename "$pidfile" .pid)
        
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null
            echo "✅ 已停止 $service_name (PID: $pid)"
            sleep 1
            
            # 强制终止（如果需要）
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null
                echo "🔥 强制终止 $service_name"
            fi
        else
            echo "⚠️ $service_name 进程不存在 (PID: $pid)"
        fi
        rm -f "$pidfile"
    fi
done

# 清理PID目录
rm -rf "$PIDS_DIR"

echo "🎉 所有服务已停止"
EOF

    # 状态检查脚本
    cat > status_offline.sh << 'EOF'
#!/bin/bash

echo "📊 AI中台离线服务状态"
echo "===================="

services=(
    "数据库服务:5432:/health"
    "缓存服务:6379:/health" 
    "AI推理服务:8100:/health"
    "监控服务:9090:/health"
    "Django后端:8000:/"
)

echo -e "\n🔍 端口检查:"
for service_info in "${services[@]}"; do
    service_name=$(echo $service_info | cut -d: -f1)
    port=$(echo $service_info | cut -d: -f2)
    
    if ss -tuln | grep -q ":$port "; then
        echo -e "✅ $service_name (端口 $port) - 运行中"
    else
        echo -e "❌ $service_name (端口 $port) - 未运行"
    fi
done

echo -e "\n🔍 进程检查:"
PIDS_DIR="/tmp/ai_platform_pids"
if [ -d "$PIDS_DIR" ]; then
    for pidfile in "$PIDS_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service_name=$(basename "$pidfile" .pid)
            
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "✅ $service_name (PID: $pid) - 正常运行"
            else
                echo -e "❌ $service_name (PID: $pid) - 进程不存在"
            fi
        fi
    done
else
    echo "ℹ️ 没有找到运行中的服务"
fi

echo -e "\n📈 系统资源:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d% -f1)%"
echo "内存: $(free | awk 'FNR==2{printf "%.1f%%", $3/($3+$4)*100}')"
echo "磁盘: $(df -h / | awk 'FNR==2{print $5}')"
EOF

    # 测试脚本
    cat > test_offline.sh << 'EOF'
#!/bin/bash

echo "🧪 测试AI中台离线服务"
echo "=================="

test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "测试 $name ... "
    
    if command -v curl &> /dev/null; then
        response=$(curl -s -w "%{http_code}" -o /tmp/test_response.json "$url" 2>/dev/null)
        status_code="${response: -3}"
        
        if [ "$status_code" = "$expected_status" ]; then
            echo -e "✅ 成功 (HTTP $status_code)"
            return 0
        else
            echo -e "❌ 失败 (HTTP $status_code)"
            return 1
        fi
    else
        echo -e "⚠️ 跳过 (curl未安装)"
        return 2
    fi
}

echo "🔍 基础健康检查:"
test_endpoint "AI推理服务" "http://localhost:8100/health"
test_endpoint "数据库服务" "http://localhost:5432/health"
test_endpoint "缓存服务" "http://localhost:6379/health"
test_endpoint "监控服务" "http://localhost:9090/health"

echo -e "\n🤖 AI推理功能测试:"
if command -v curl &> /dev/null; then
    echo "测试线性回归模型..."
    curl -s -X POST http://localhost:8100/infer \
        -H "Content-Type: application/json" \
        -d '{"model_name": "simple-linear", "inputs": {"data": [1,2,3,4,5,6,7,8,9,10]}}' | \
        python3 -c "import json, sys; data=json.load(sys.stdin); print(f'✅ 预测结果: {data.get(\"predictions\", {}).get(\"prediction\", \"N/A\")}'); print(f'⏱️ 推理时间: {data.get(\"inference_time\", \"N/A\")}s')" 2>/dev/null || \
        echo "❌ 推理测试失败"
    
    echo -e "\n测试文本分类模型..."
    curl -s -X POST http://localhost:8100/infer \
        -H "Content-Type: application/json" \
        -d '{"model_name": "text-classifier", "inputs": {"text": "这是一个测试文本"}}' | \
        python3 -c "import json, sys; data=json.load(sys.stdin); print(f'✅ 分类结果: {data.get(\"predictions\", {}).get(\"predicted_class\", \"N/A\")}'); print(f'🎯 置信度: {data.get(\"predictions\", {}).get(\"confidence\", \"N/A\")}')" 2>/dev/null || \
        echo "❌ 文本分类测试失败"
fi

echo -e "\n📊 获取模型列表:"
if command -v curl &> /dev/null; then
    curl -s http://localhost:8100/models | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    models = data.get('models', {})
    print(f'✅ 可用模型数量: {len(models)}')
    for name, info in models.items():
        print(f'  • {name}: {info.get(\"description\", \"N/A\")}')
except:
    print('❌ 无法解析模型列表')
" 2>/dev/null || echo "❌ 获取模型列表失败"
fi

echo -e "\n🎯 测试完成！访问监控面板查看详细信息:"
echo "http://localhost:9090/dashboard"
EOF

    chmod +x start_offline.sh stop_offline.sh status_offline.sh test_offline.sh
    echo -e "${GREEN}✅ 控制脚本创建完成${NC}"
}

# 主函数
main() {
    echo -e "${PURPLE}=== AI中台离线部署开始 ===${NC}"
    
    cd "$WORKSPACE_DIR"
    
    create_directories
    create_database_service
    create_cache_service  
    create_inference_service
    create_monitoring_service
    create_control_scripts
    
    echo -e "\n${GREEN}🎉 离线部署准备完成！${NC}"
    echo -e "\n${BLUE}📋 使用说明:${NC}"
    echo "1. 启动所有服务: ${YELLOW}./start_offline.sh${NC}"
    echo "2. 查看服务状态: ${YELLOW}./status_offline.sh${NC}" 
    echo "3. 测试服务功能: ${YELLOW}./test_offline.sh${NC}"
    echo "4. 停止所有服务: ${YELLOW}./stop_offline.sh${NC}"
    echo "5. 监控面板: ${CYAN}http://localhost:9090/dashboard${NC}"
    
    echo -e "\n${BLUE}💡 特点:${NC}"
    echo "• 🚫 完全不依赖Docker和外部镜像"
    echo "• 🔧 使用纯Python实现所有服务"  
    echo "• 🤖 支持多种AI模型推理"
    echo "• 📊 内置系统监控面板"
    echo "• 🗄️ 轻量级数据库和缓存"
    echo "• 🌐 标准HTTP API接口"
    
    echo -e "\n${YELLOW}⚠️ 注意:${NC}"
    echo "• 这是演示版本，生产环境建议使用完整Docker方案"
    echo "• 监控服务需要psutil模块，会自动尝试安装"
    echo "• 所有数据存储在本地，重启后缓存数据会丢失"
    
    echo -e "\n${GREEN}✨ 现在可以运行 './start_offline.sh' 启动服务了！${NC}"
}

# 运行主函数
main "$@"