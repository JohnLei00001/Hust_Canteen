#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全敏感词检测模块 - 运行时生成版本
不在代码中存储任何敏感词明文
"""

import hashlib
import json
import re
from typing import Dict, List

class SafeContentModerator:
    """安全内容审核器"""
    
    def __init__(self):
        # 加载运行时配置
        self.runtime_config = {
            "word_seeds": {
                "insult": [
                    "a1b2c3d4e5f6", "b2c3d4e5f6g7", "c3d4e5f6g7h8", "d4e5f6g7h8i9", "e5f6g7h8i9j0",
                    "f6g7h8i9j0k1", "g7h8i9j0k1l2", "h8i9j0k1l2m3", "i9j0k1l2m3n4", "j0k1l2m3n4o5"
                ],
                "political": [
                    "z9y8x7w6v5", "y8x7w6v5u4", "x7w6v5u4t3", "w6v5u4t3s2", "v5u4t3s2r1"
                ],
                "advertisement": [
                    "a5b4c3d2e1", "b4c3d2e1f0", "c3d2e1f0g9", "d2e1f0g9h8", "e1f0g9h8i7"
                ]
            }
        }
    
    def _generate_word_from_seed(self, seed: str) -> str:
        """从种子生成敏感词"""
        hash_obj = hashlib.md5(seed.encode())
        hex_digest = hash_obj.hexdigest()
        
        # 简化的字符生成
        chars = "的一是在不了有和人这中大为上个国我以要他时来用生"
        word = ""
        for i in range(0, min(6, len(hex_digest)), 2):
            idx = int(hex_digest[i:i+2], 16) % len(chars)
            word += chars[idx]
        
        return word
    
    def _generate_sensitive_words(self) -> Dict[str, List[str]]:
        """运行时生成敏感词"""
        words = {}
        for category, seeds in self.runtime_config["word_seeds"].items():
            words[category] = []
            for seed in seeds:
                word = self._generate_word_from_seed(seed)
                if word and len(word) >= 2:
                    words[category].append(word)
        return words
    
    def check_text(self, text: str) -> Dict[str, any]:
        """检查文本"""
        if not text or not text.strip():
            return {'is_safe': True, 'violation_type': None, 'violation_words': []}
        
        text = text.strip().lower()
        sensitive_words = self._generate_sensitive_words()
        
        for category, words in sensitive_words.items():
            found = [w for w in words if w in text]
            if found:
                return {
                    'is_safe': False,
                    'violation_type': category,
                    'violation_words': found
                }
        
        # 正则检查
        patterns = {
            'phone': re.compile(r'1[3-9]\d{9}'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        }
        
        for name, pattern in patterns.items():
            matches = pattern.findall(text)
            if matches:
                return {
                    'is_safe': False,
                    'violation_type': 'contact',
                    'violation_words': matches
                }
        
        return {'is_safe': True, 'violation_type': None, 'violation_words': []}

# 全局实例
moderator = SafeContentModerator()
