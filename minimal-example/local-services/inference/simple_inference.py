#!/usr/bin/env python3
"""
简化版AI推理服务 - 无外部依赖
"""

import json
import http.server
import socketserver
import time
import random
from datetime import datetime
import urllib.parse

class SimpleInferenceHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "service": "AI中台简化推理服务",
                "status": "healthy", 
                "timestamp": datetime.now().isoformat(),
                "models": ["simple-linear", "simple-cnn", "text-classifier"],
                "endpoints": ["/", "/health", "/models", "/infer"]
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        
        elif self.path == "/models":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            models = {
                "simple-linear": {"type": "regression", "input_shape": [10], "output_shape": [1]},
                "simple-cnn": {"type": "classification", "input_shape": [224, 224, 3], "output_shape": [1000]},
                "text-classifier": {"type": "text", "input_type": "string", "output_classes": 5}
            }
            self.wfile.write(json.dumps({"models": models}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == "/infer":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                result = self.mock_inference(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"error": str(e)}
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        # 处理CORS预检请求
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def mock_inference(self, request_data):
        """模拟AI推理过程"""
        model_name = request_data.get("model_name", "simple-linear")
        inputs = request_data.get("inputs", {})
        
        # 模拟推理延迟
        time.sleep(random.uniform(0.01, 0.05))
        
        start_time = time.time()
        
        if "linear" in model_name:
            # 线性回归模拟
            input_data = inputs.get("data", [1,2,3,4,5,6,7,8,9,10])
            prediction = sum(input_data) * 0.1 + random.uniform(-0.1, 0.1)
            result = {"prediction": round(prediction, 4)}
            
        elif "cnn" in model_name:
            # CNN分类模拟
            predictions = [random.random() for _ in range(10)]
            result = {
                "class_id": predictions.index(max(predictions)),
                "confidence": max(predictions),
                "probabilities": [round(p, 4) for p in predictions]
            }
            
        elif "text" in model_name:
            # 文本分类模拟
            text = inputs.get("text", "")
            sentiments = ["positive", "negative", "neutral", "mixed", "unknown"]
            result = {
                "sentiment": random.choice(sentiments),
                "confidence": round(random.uniform(0.7, 0.99), 4),
                "text_length": len(text)
            }
        else:
            result = {"message": "Unknown model", "default_output": random.random()}
        
        inference_time = time.time() - start_time
        
        return {
            "model_name": model_name,
            "result": result,
            "inference_time": round(inference_time, 6),
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }

if __name__ == "__main__":
    PORT = 8100
    print(f"🚀 AI推理服务启动在端口 {PORT}")
    print(f"📱 访问地址: http://localhost:{PORT}")
    print(f"🧪 健康检查: http://localhost:{PORT}/health")
    print(f"📋 模型列表: http://localhost:{PORT}/models")
    print("按 Ctrl+C 停止服务")
    
    try:
        with socketserver.TCPServer(("", PORT), SimpleInferenceHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ 服务已停止")
