"""
校园食堂系统安全配置
包含所有安全相关的配置参数
"""

import os
from datetime import timedelta

class SecurityConfig:
    """安全配置类"""
    
    # Flask安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secure-secret-key-change-this-in-production'
    SESSION_COOKIE_SECURE = True  # 仅HTTPS
    SESSION_COOKIE_HTTPONLY = True  # 防止XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF防护
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # 会话有效期
    
    # 密码安全
    BCRYPT_LOG_ROUNDS = 12  # 哈希强度
    
    # 数据库安全
    DB_POOL_SIZE = 10
    DB_POOL_TIMEOUT = 30
    DB_POOL_RECYCLE = 3600
    
    # 文件上传安全
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 速率限制配置
    RATE_LIMITS = {
        'login': {'limit': 5, 'window': 60},  # 每分钟5次登录尝试
        'register': {'limit': 3, 'window': 60},  # 每分钟3次注册
        'api': {'limit': 100, 'window': 60},  # 每分钟100次API调用
        'password_reset': {'limit': 3, 'window': 3600},  # 每小时3次密码重置
    }
    
    # DDoS防护配置
    DDOS_PROTECTION = {
        'max_requests_per_minute': 60,
        'max_requests_per_second': 5,
        'block_duration': 300,  # 5分钟
        'whitelist': ['127.0.0.1', '::1'],  # 仅本地白名单，其余全网开放
    }
    
    # 内容安全策略(CSP)
    CSP = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com"],
        'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'", "fonts.gstatic.com"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
    }
    
    # 安全头配置
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
    }
    
    # 日志配置
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'security': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(ip)s - %(user)s'
            }
        },
        'handlers': {
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/security.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'formatter': 'security'
            }
        },
        'loggers': {
            'security': {
                'handlers': ['security_file'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    # 敏感数据检测
    SENSITIVE_DATA_PATTERNS = [
        r'\b\d{15}\d{2}[0-9Xx]\b',  # 身份证号
        r'\b1[3-9]\d{9}\b',  # 手机号
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 邮箱
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # 银行卡号
    ]
    
    # 安全监控配置
    SECURITY_MONITORING = {
        'enable_real_time': True,
        'alert_threshold': {
            'failed_logins': 5,  # 5分钟内5次失败登录
            'sql_injection_attempts': 3,  # 3次SQL注入尝试
            'xss_attempts': 3,  # 3次XSS尝试
            'brute_force': 10,  # 10分钟内10次暴力破解
        },
        'email_alerts': True,
        'admin_email': 'admin@canteen-system.com',
    }

# 生产环境配置
class ProductionConfig(SecurityConfig):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
# 开发环境配置
class DevelopmentConfig(SecurityConfig):
    DEBUG = True
    TESTING = True
    SESSION_COOKIE_SECURE = False  # 开发环境允许HTTP