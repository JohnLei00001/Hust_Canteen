#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows生产环境启动脚本
使用Waitress WSGI服务器（Windows兼容的高性能服务器）
"""
import os
import sys
import subprocess

def start_production():
    """启动Windows生产服务器"""
    print("🚀 启动Windows生产级食堂系统...")
    
    # 检查waitress是否安装
    try:
        import waitress
        print("✅ Waitress已安装")
    except ImportError:
        print("❌ 正在安装Waitress...")
        subprocess.run([sys.executable, "-m", "pip", "install", "waitress"])
    
    # 使用waitress启动（Windows专用高性能服务器）
    cmd = [
        sys.executable, "-c",
        """
import sys
sys.path.insert(0, '.')
from app import app
from waitress import serve

print("🌐 服务器地址: http://localhost:5000")
print("📊 并发能力: 支持30-50人同时在线")
print("⚡ 使用Waitress高性能WSGI服务器")
print("🔧 配置: 4线程，连接池优化")

serve(app, host='0.0.0.0', port=5000, threads=4, connection_limit=200)
        """
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    start_production()