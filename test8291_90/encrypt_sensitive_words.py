#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敏感词加密工具
用于将敏感词列表加密为密文，供加密版内容审核器使用
"""

import json
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import getpass
import os

def generate_key_from_password(password: str, salt: bytes = None) -> bytes:
    """从密码生成加密密钥"""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_sensitive_words(words: list, password: str) -> dict:
    """加密敏感词列表"""
    key, salt = generate_key_from_password(password)
    f = Fernet(key)
    
    # 将敏感词列表转换为JSON字符串
    words_json = json.dumps(words, ensure_ascii=False)
    encrypted = f.encrypt(words_json.encode())
    
    return {
        'encrypted_data': base64.b64encode(encrypted).decode(),
        'salt': base64.b64encode(salt).decode()
    }

def decrypt_sensitive_words(encrypted_data: dict, password: str) -> list:
    """解密敏感词列表"""
    try:
        encrypted_bytes = base64.b64decode(encrypted_data['encrypted_data'])
        salt = base64.b64decode(encrypted_data['salt'])
        
        key, _ = generate_key_from_password(password, salt)
        f = Fernet(key)
        
        decrypted = f.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode())
    except Exception as e:
        print(f"解密失败: {e}")
        return []

def interactive_encrypt():
    """交互式加密工具"""
    print("=== 敏感词加密工具 ===")
    print("请输入敏感词，每行一个，输入空行结束:")
    
    words = []
    while True:
        word = input("敏感词: ").strip()
        if not word:
            break
        words.append(word)
    
    if not words:
        print("没有输入敏感词")
        return
    
    password = getpass.getpass("请输入加密密码: ")
    confirm_password = getpass.getpass("请确认密码: ")
    
    if password != confirm_password:
        print("密码不匹配！")
        return
    
    if len(password) < 6:
        print("密码长度至少6位")
        return
    
    encrypted = encrypt_sensitive_words(words, password)
    
    print("\n=== 加密结果 ===")
    print("请将以下内容保存到 encrypted_sensitive_words.json:")
    print(json.dumps(encrypted, ensure_ascii=False, indent=2))
    
    # 保存到文件
    with open('encrypted_sensitive_words.json', 'w', encoding='utf-8') as f:
        json.dump(encrypted, f, ensure_ascii=False, indent=2)
    
    print("\n加密完成！文件已保存到: encrypted_sensitive_words.json")
    
    # 验证解密
    test_decrypt = input("是否要验证解密？(y/n): ").strip().lower()
    if test_decrypt == 'y':
        test_password = getpass.getpass("请输入密码验证: ")
        decrypted = decrypt_sensitive_words(encrypted, test_password)
        if decrypted:
            print("验证成功！解密后的敏感词:")
            for word in decrypted:
                print(f"  - {word}")
        else:
            print("验证失败！密码错误或数据损坏")

if __name__ == "__main__":
    interactive_encrypt()