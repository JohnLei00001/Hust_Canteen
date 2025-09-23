#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全防护工具模块
提供输入验证、SQL注入防护、XSS防护等功能
"""
import re
import html
import hashlib
import secrets
from functools import wraps
from flask import request, jsonify, session

class SecurityUtils:
    """安全防护工具类"""
    
    @staticmethod
    def validate_input(data, input_type='text', max_length=None):
        """输入验证和清理"""
        if not data:
            return None
            
        # 基本清理
        data = str(data).strip()
        
        # 长度限制
        if max_length and len(data) > max_length:
            return None
            
        # 类型验证
        if input_type == 'email':
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data):
                return None
        elif input_type == 'username':
            if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', data):
                return None
        elif input_type == 'phone':
            if not re.match(r'^1[3-9]\d{9}$', data):
                return None
        elif input_type == 'number':
            try:
                return int(data)
            except ValueError:
                return None
                
        # 转义HTML防止XSS
        data = html.escape(data)
        return data
    
    @staticmethod
    def sanitize_html(text):
        """清理HTML内容"""
        if not text:
            return ""
            
        # 移除危险标签和属性
        dangerous_tags = ['script', 'iframe', 'object', 'embed', 'form']
        dangerous_attrs = ['onload', 'onerror', 'onclick', 'onmouseover']
        
        text = str(text)
        
        # 移除危险标签
        for tag in dangerous_tags:
            text = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', text, flags=re.IGNORECASE)
            text = re.sub(f'<{tag}[^>]*/>', '', text, flags=re.IGNORECASE)
            
        # 移除危险属性
        for attr in dangerous_attrs:
            text = re.sub(f'{attr}="[^"]*"', '', text, flags=re.IGNORECASE)
            text = re.sub(f"{attr}='[^']*'", '', text, flags=re.IGNORECASE)
            
        return text
    
    @staticmethod
    def generate_csrf_token():
        """生成CSRF令牌"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password):
        """密码哈希"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000).hex()
    
    @staticmethod
    def rate_limit(max_requests=100, window=3600):
        """速率限制装饰器"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
                key = f"rate_limit:{client_ip}:{f.__name__}"
                
                # 这里可以集成Redis进行分布式限流
                # 简化版本：使用内存存储
                from collections import defaultdict
                import time
                
                if not hasattr(rate_limit, 'storage'):
                    rate_limit.storage = defaultdict(list)
                
                now = time.time()
                requests = rate_limit.storage[key]
                
                # 清理过期请求
                requests[:] = [req for req in requests if now - req < window]
                
                if len(requests) >= max_requests:
                    return jsonify({'error': '请求过于频繁，请稍后再试'}), 429
                
                requests.append(now)
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# 安全装饰器
def require_auth(f):
    """需要认证的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('is_guest'):
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """需要管理员权限的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

def validate_json(f):
    """验证JSON输入的装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': '需要JSON格式数据'}), 400
        return f(*args, **kwargs)
    return decorated_function