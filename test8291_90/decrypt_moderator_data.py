#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敏感数据解密工具
"""

import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_key(password: str = "secure_moderator_2024"):
    """生成相同的密钥"""
    import base64
    salt = b'secure_salt_for_moderator_2024'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def decrypt_sensitive_data():
    """解密敏感数据"""
    try:
        with open('encrypted_moderator_data.json', 'r', encoding='utf-8') as f:
            encrypted_info = json.load(f)
        
        encrypted_b64 = encrypted_info['encrypted_data']
        encrypted_data = base64.b64decode(encrypted_b64)
        
        key = generate_key()
        cipher = Fernet(key)
        
        decrypted = cipher.decrypt(encrypted_data)
        sensitive_data = json.loads(decrypted.decode())
        
        return sensitive_data
        
    except Exception as e:
        print(f"解密失败: {e}")
        return None

if __name__ == "__main__":
    data = decrypt_sensitive_data()
    if data:
        print("敏感数据解密成功")
        print(f"包含 {len(data.get('sensitive_words', {}))} 类敏感词")
