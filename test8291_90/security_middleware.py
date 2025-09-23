#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全中间件模块
提供HTTP安全头、CORS、内容安全策略等防护
"""
from flask import Flask, request, g
from datetime import datetime
import logging

class SecurityMiddleware:
    """安全中间件类"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化安全中间件"""
        
        @app.before_request
        def security_headers():
            """设置安全HTTP头"""
            g.start_time = datetime.now()
            
        @app.after_request
        def add_security_headers(response):
            """添加安全HTTP头"""
            
            # 内容安全策略 (CSP)
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
            
            # 安全HTTP头
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = csp_policy
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
            
            # 防止缓存问题
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            # 移除服务器信息
            response.headers.pop('Server', None)
            
            return response
        
        # 设置CORS策略
        @app.after_request
        def add_cors_headers(response):
            """添加CORS头"""
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '')
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response

# 安全日志记录器
class SecurityLogger:
    """安全日志记录"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_login_attempt(self, username, success, ip_address):
        """记录登录尝试"""
        status = "成功" if success else "失败"
        self.logger.warning(f"登录{status}: 用户={username}, IP={ip_address}")
    
    def log_suspicious_activity(self, activity, ip_address, user_agent):
        """记录可疑活动"""
        self.logger.warning(f"可疑活动: {activity}, IP={ip_address}, UA={user_agent}")
    
    def log_security_breach(self, breach_type, details):
        """记录安全事件"""
        self.logger.error(f"安全事件: {breach_type}, 详情: {details}")
    
    def log_security_event(self, event_type, details):
        """通用安全事件记录"""
        level_map = {
            'successful_login': logging.INFO,
            'failed_login': logging.WARNING,
            'login_error': logging.ERROR,
            'login_rate_limit': logging.WARNING,
            'security_breach': logging.ERROR
        }
        
        level = level_map.get(event_type, logging.INFO)
        self.logger.log(level, f"安全事件: {event_type}, 详情: {details}")