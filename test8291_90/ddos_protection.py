#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDoS防护模块
提供基于IP的速率限制和连接管理
"""
import time
import threading
from collections import defaultdict
from functools import wraps
from flask import request, jsonify, session
import logging

class DDoSProtection:
    def __init__(self):
        self.request_counts = defaultdict(list)  # IP -> [timestamps]
        self.blocked_ips = set()
        self.lock = threading.Lock()
        
        # 配置参数
        self.max_requests_per_minute = 60  # 每分钟最大请求数
        self.max_requests_per_second = 5  # 每秒最大请求数
        self.block_duration = 300  # 封禁时长（秒）
        self.cleanup_interval = 3600  # 清理间隔（秒）
        
        # 启动清理线程
        self.start_cleanup_thread()
        
        # 设置日志
        self.logger = logging.getLogger('ddos_protection')
        handler = logging.FileHandler('ddos_protection.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def is_allowed(self, ip_address):
        """检查IP是否允许访问"""
        with self.lock:
            # 检查是否在封禁列表
            if ip_address in self.blocked_ips:
                return False
                
            current_time = time.time()
            
            # 清理过期记录
            self.request_counts[ip_address] = [
                timestamp for timestamp in self.request_counts[ip_address]
                if current_time - timestamp < 60  # 保留1分钟内的记录
            ]
            
            # 检查每分钟请求数
            if len(self.request_counts[ip_address]) >= self.max_requests_per_minute:
                self.block_ip(ip_address)
                self.logger.warning(f"IP {ip_address} 被封禁 - 超过每分钟请求限制")
                return False
            
            # 检查每秒请求数
            recent_requests = [
                timestamp for timestamp in self.request_counts[ip_address]
                if current_time - timestamp < 1
            ]
            
            if len(recent_requests) >= self.max_requests_per_second:
                self.block_ip(ip_address)
                self.logger.warning(f"IP {ip_address} 被封禁 - 超过每秒请求限制")
                return False
            
            # 记录当前请求
            self.request_counts[ip_address].append(current_time)
            return True

    def block_ip(self, ip_address):
        """封禁IP地址"""
        with self.lock:
            self.blocked_ips.add(ip_address)
            # 设置定时解封
            threading.Timer(self.block_duration, self.unblock_ip, [ip_address]).start()

    def unblock_ip(self, ip_address):
        """解封IP地址"""
        with self.lock:
            self.blocked_ips.discard(ip_address)
            self.request_counts.pop(ip_address, None)
            self.logger.info(f"IP {ip_address} 已解封")

    def cleanup_thread(self):
        """定期清理过期数据"""
        while True:
            time.sleep(self.cleanup_interval)
            with self.lock:
                current_time = time.time()
                for ip in list(self.request_counts.keys()):
                    self.request_counts[ip] = [
                        timestamp for timestamp in self.request_counts[ip]
                        if current_time - timestamp < 60
                    ]
                    if not self.request_counts[ip]:
                        del self.request_counts[ip]

    def start_cleanup_thread(self):
        """启动清理线程"""
        cleanup = threading.Thread(target=self.cleanup_thread, daemon=True)
        cleanup.start()

    def get_stats(self):
        """获取防护统计信息"""
        with self.lock:
            return {
                'blocked_ips': len(self.blocked_ips),
                'active_connections': len(self.request_counts),
                'uptime': time.time() - getattr(self, 'start_time', time.time())
            }

    def rate_limit(self, max_requests=10, window=60):
        """装饰器：限制请求速率"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                ip_address = request.remote_addr
                
                if not self.is_allowed(ip_address):
                    return jsonify({
                        'error': '请求过于频繁，请稍后再试',
                        'retry_after': self.block_duration
                    }), 429
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator

# 全局DDoS防护实例
ddos_protection = DDoSProtection()

def rate_limit(max_requests=10, window=60):
    """简化版速率限制装饰器"""
    return ddos_protection.rate_limit(max_requests, window)

# 登录尝试限制
class LoginProtection:
    def __init__(self):
        self.failed_attempts = defaultdict(list)
        self.lock = threading.Lock()
        self.max_attempts = 5
        self.lockout_duration = 900  # 15分钟

    def check_login_attempt(self, ip_address):
        """检查登录尝试"""
        with self.lock:
            current_time = time.time()
            
            # 清理过期记录
            self.failed_attempts[ip_address] = [
                timestamp for timestamp in self.failed_attempts[ip_address]
                if current_time - timestamp < self.lockout_duration
            ]
            
            return len(self.failed_attempts[ip_address]) < self.max_attempts

    def record_failed_attempt(self, ip_address):
        """记录失败尝试"""
        with self.lock:
            self.failed_attempts[ip_address].append(time.time())

    def record_successful_login(self, ip_address):
        """清除失败记录"""
        with self.lock:
            self.failed_attempts.pop(ip_address, None)

# 登录保护实例
login_protection = LoginProtection()