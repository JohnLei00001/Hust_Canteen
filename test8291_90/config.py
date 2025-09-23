#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CentOS7云服务器配置文件
数据库和系统配置
"""

import os

# CentOS7云服务器数据库配置
DB_CONFIG = {
    'host': 'localhost',  # 数据库在同一服务器
    'user': 'canteen_user',  # 建议创建专用用户
    'password': os.environ.get('DB_PASSWORD', 'your_secure_password'),  # 从环境变量读取
    'database': 'hust_canteen',
    'port': 3306,
    'charset': 'utf8mb4',
    'pool_name': 'canteen_pool',
    'pool_size': 10,
    'pool_reset_session': True
}

# 生产环境安全配置
class ProductionConfig:
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secure-secret-key'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 文件上传配置
    UPLOAD_FOLDER = '/var/www/canteen/test8291_90/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 会话配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# 开发环境配置
class DevelopmentConfig:
    DEBUG = True
    TESTING = False
    SECRET_KEY = 'dev-secret-key'
    
    # 开发数据库配置
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # 文件上传配置
    UPLOAD_FOLDER = '/var/www/canteen/test8291_90/static/uploads'
    SESSION_COOKIE_SECURE = False  # 开发环境允许HTTP

# 根据环境选择配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}