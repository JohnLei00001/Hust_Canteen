#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密版内容审核器
使用加密后的敏感词列表进行内容审核
敏感词已加密存储，无法直接读取
"""

import json
import base64
import hashlib
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class EncryptedContentModerator:
    def __init__(self, password: str = "helloworld"):
        """初始化加密内容审核器，使用用户指定的密码"""
        self.password = password
        self.encrypted_data = self._load_encrypted_data()
        self.sensitive_patterns = []
        self._load_sensitive_patterns()
    
    def _get_default_password(self) -> str:
        """获取默认密码（可以修改为自己的密码）"""
        # 警告：这是示例密码，请修改为自己的密码
        return "your_secure_password_here_123"
    
    def _load_encrypted_data(self) -> dict:
        """加载加密的敏感词数据"""
        encrypted_file = 'encrypted_sensitive_words.json'
        if not os.path.exists(encrypted_file):
            # 使用预设的加密数据（敏感词已加密）
            return self._get_default_encrypted_data()
        
        try:
            with open(encrypted_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载加密数据失败: {e}")
            return self._get_default_encrypted_data()
    
    def _get_default_encrypted_data(self) -> dict:
        """默认加密数据（敏感词已加密）"""
        # 这是敏感词加密后的数据，无法直接读取原文
        return {
            "encrypted_data": "gAAAAABn...加密数据...",
            "salt": "...盐值..."
        }
    
    def _generate_key_from_password(self, salt: bytes) -> bytes:
        """从密码生成解密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return key
    
    def _decrypt_sensitive_words(self) -> list:
        """解密敏感词列表"""
        try:
            encrypted_bytes = base64.b64decode(self.encrypted_data['encrypted_data'])
            salt = base64.b64decode(self.encrypted_data['salt'])
            
            key = self._generate_key_from_password(salt)
            f = Fernet(key)
            
            decrypted = f.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            print(f"解密敏感词失败: {e}")
            return []
    
    def _load_sensitive_patterns(self):
        """加载敏感词模式"""
        sensitive_words = self._decrypt_sensitive_words()
        
        # 创建正则表达式模式
        for word in sensitive_words:
            if word and len(word) > 1:
                # 创建不区分大小写的正则表达式
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                self.sensitive_patterns.append((word, pattern))
    
    def moderate_text(self, text: str) -> dict:
        """
        审核文本内容
        
        Args:
            text: 要审核的文本
            
        Returns:
            dict: 审核结果
        """
        if not text or not isinstance(text, str):
            return {
                'is_safe': True,
                'sensitive_words': [],
                'masked_text': text,
                'risk_level': 'low'
            }
        
        found_words = []
        masked_text = text
        
        # 检查每个敏感词
        for original_word, pattern in self.sensitive_patterns:
            matches = pattern.findall(text)
            if matches:
                found_words.extend(matches)
                # 用星号替换敏感词
                masked_text = pattern.sub('*' * len(original_word), masked_text)
        
        # 确定风险等级
        risk_level = 'low'
        if found_words:
            if len(found_words) >= 3:
                risk_level = 'high'
            elif len(found_words) >= 2:
                risk_level = 'medium'
            else:
                risk_level = 'low'
        
        return {
            'is_safe': len(found_words) == 0,
            'sensitive_words': list(set(found_words)),
            'masked_text': masked_text,
            'risk_level': risk_level,
            'word_count': len(found_words)
        }
    
    def moderate_batch(self, texts: list) -> list:
        """批量审核文本"""
        return [self.moderate_text(text) for text in texts]
    
    def get_stats(self) -> dict:
        """获取审核器统计信息"""
        return {
            'encrypted_word_count': len(self.sensitive_patterns),
            'encryption_method': 'Fernet (AES 128)',
            'key_derivation': 'PBKDF2-HMAC-SHA256',
            'iterations': 100000,
            'data_source': 'encrypted_sensitive_words.json'
        }

# 全局实例
_moderator_instance = None

def get_moderator():
    """获取全局内容审核器实例"""
    global _moderator_instance
    if _moderator_instance is None:
        _moderator_instance = EncryptedContentModerator()
    return _moderator_instance

def moderate_text(text: str) -> dict:
    """快速审核文本"""
    return get_moderator().moderate_text(text)

def moderate_batch(texts: list) -> list:
    """快速批量审核"""
    return get_moderator().moderate_batch(texts)

if __name__ == "__main__":
    # 测试加密内容审核器
    moderator = EncryptedContentModerator()
    
    # 显示统计信息
    stats = moderator.get_stats()
    print("=== 加密内容审核器信息 ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 测试审核
    test_texts = [
        "这是一个测试文本",
        "包含敏感词的文本",
        "正常的内容没有任何问题"
    ]
    
    print("\n=== 测试审核 ===")
    for text in test_texts:
        result = moderator.moderate_text(text)
        print(f"原文: {text}")
        print(f"审核结果: {result}")
        print()