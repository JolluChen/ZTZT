"""
本地开发环境启动脚本
不需要Docker，使用SQLite数据库
"""
import os
import sys
import subprocess

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_local')

def main():
    print("=== AI平台本地开发环境启动 ===")
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 切换到backend目录
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    try:
        # 安装依赖
        print("\n1. 安装Python依赖...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        
        # 创建迁移
        print("\n2. 创建数据库迁移...")
        subprocess.run([sys.executable, 'manage.py', 'makemigrations'], check=True)
        
        # 应用迁移
        print("\n3. 应用数据库迁移...")
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        # 创建超级用户（可选）
        print("\n4. 创建超级用户（可选，按Ctrl+C跳过）...")
        try:
            subprocess.run([sys.executable, 'manage.py', 'createsuperuser'], timeout=30)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            print("跳过创建超级用户")
        
        # 启动开发服务器
        print("\n5. 启动Django开发服务器...")
        print("服务器地址: http://127.0.0.1:8000")
        print("管理后台: http://127.0.0.1:8000/admin")
        print("API文档: http://127.0.0.1:8000/api")
        print("\n按 Ctrl+C 停止服务器")
        
        subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])
        
    except subprocess.CalledProcessError as e:
        print(f"错误: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
        return 0

if __name__ == '__main__':
    sys.exit(main())
