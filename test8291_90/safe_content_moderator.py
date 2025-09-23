#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全敏感词检测模块 - 加密敏感词版本
使用加密敏感词进行内容审核，敏感词不会以明文形式存储
"""

import json
import logging
from encrypted_content_moderator import EncryptedContentModerator

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeContentModerator:
    """安全内容审核包装器"""
    
    def __init__(self, password: str = "helloworld", config_file: str = "moderator_config.json"):
        """初始化安全审核器，使用指定密码"""
        try:
            self.moderator = EncryptedContentModerator(password=password)
            logger.info("安全内容审核器初始化成功")
        except Exception as e:
            logger.error(f"审核器初始化失败: {e}")
            raise
    
    def check_text(self, text: str) -> dict:
        """
        检查文本安全性
        
        Args:
            text: 要检查的内容
            
        Returns:
            dict: 检查结果
        """
        try:
            result = self.moderator.moderate_text(text)
            
            # 转换为兼容格式
            return {
                'is_safe': result['is_safe'],
                'violation_type': result['risk_level'] if not result['is_safe'] else None,
                'violation_words': result['sensitive_words'],
                'masked_text': result['masked_text']
            }
            
        except Exception as e:
            logger.error(f"内容审核失败: {e}")
            return {
                'is_safe': True,  # 出错时默认安全
                'violation_type': None,
                'violation_words': [],
                'masked_text': text,
                'error': str(e)
            }
    
    def check_review(self, review_text: str, rating: int = None) -> dict:
        """检查评论内容"""
        result = self.check_text(review_text)
        
        # 额外的评论检查逻辑
        if rating and rating < 1:
            result['is_safe'] = False
            result['violation_type'] = 'invalid_rating'
            result['violation_words'] = ['invalid_rating']
        
        return result
    
    def check_comment(self, comment_text: str) -> dict:
        """检查评论回复"""
        return self.check_text(comment_text)
    
    def batch_check(self, contents: list) -> list:
        """批量检查内容"""
        return [self.check_text(content) for content in contents]
    
    def get_system_info(self) -> dict:
        """获取系统信息"""
        try:
            stats = self.moderator.get_stats()
            return {
                'system_status': 'active',
                'encryption_enabled': True,
                'word_count': stats.get('encrypted_word_count', 0),
                'security_level': 'high',
                'encryption_method': stats.get('encryption_method', 'Fernet'),
                'data_source': stats.get('data_source', 'encrypted')
            }
        except Exception as e:
            return {
                'system_status': 'error',
                'encryption_enabled': True,
                'error': str(e)
            }

# 全局实例
_safe_moderator = None

def get_safe_moderator():
    """获取全局安全审核器实例"""
    global _safe_moderator
    if _safe_moderator is None:
        _safe_moderator = SafeContentModerator()
    return _safe_moderator

def check_text_safe(text: str) -> bool:
    """快速检查内容是否安全"""
    moderator = get_safe_moderator()
    result = moderator.check_text(text)
    return result['is_safe']

def moderate_content(text: str, content_type: str = "text") -> dict:
    """完整内容审核"""
    moderator = get_safe_moderator()
    return moderator.check_text(text)

def check_comment(text: str) -> dict:
    """检查评论内容（兼容接口）"""
    moderator = get_safe_moderator()
    return moderator.check_comment(text)

def is_safe_comment(text: str) -> bool:
    """快速检查评论是否安全（兼容接口）"""
    return check_text_safe(text)
