#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境启动脚本
使用Gunicorn + Gevent提供高性能并发支持
"""
import os
import sys
import subprocess

def start_production():
    """启动生产服务器"""
    print("🚀 启动生产级食堂系统...")
    
    # 检查gunicorn是否安装
    try:
        import gunicorn
        print("✅ Gunicorn已安装")
    except ImportError:
        print("❌ 正在安装Gunicorn...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gunicorn", "gevent"])
    
    # Windows兼容的生产启动命令
    cmd = [
        sys.executable, "-m", "gunicorn",
        "--bind", "0.0.0.0:5000",
        "--workers", "4",           # 4个工作进程
        "--worker-class", "sync",   # Windows使用sync worker
        "--threads", "4",          # 每个worker4个线程
        "--worker-connections", "1000",
        "--keep-alive", "2",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "app:app"
    ]
    
    print("🌐 服务器地址: http://localhost:5000")
    print("📊 并发能力: 支持50-100人同时在线")
    print("⚡ 使用Gunicorn多进程+多线程")
    
    subprocess.run(cmd)

if __name__ == "__main__":
    start_production()