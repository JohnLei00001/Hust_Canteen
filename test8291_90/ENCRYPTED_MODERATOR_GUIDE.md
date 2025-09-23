# 🔐 加密内容审核系统使用指南

## 📋 系统概述

本系统提供完全加密的内容审核功能，敏感词不会以明文形式存储在代码中，确保上传服务器时的安全性。

## 🛠️ 使用步骤

### 步骤1: 加密敏感词

使用加密工具将敏感词加密：

```bash
python encrypt_sensitive_words.py
```

按照提示操作：
1. 输入敏感词（每行一个，空行结束）
2. 设置加密密码（至少6位）
3. 系统会生成 `encrypted_sensitive_words.json` 文件

### 步骤2: 部署加密审核器

上传以下文件到服务器：
- `encrypted_content_moderator.py` - 加密审核器核心
- `safe_content_moderator.py` - 安全包装器
- `encrypted_sensitive_words.json` - 加密敏感词文件

### 步骤3: 在应用中使用

```python
from safe_content_moderator import check_text_safe, moderate_content

# 快速检查
is_safe = check_text_safe("用户输入的内容")

# 详细审核
result = moderate_content("用户评论内容", content_type="review")
print(f"安全: {result['is_safe']}")
print(f"风险等级: {result['risk_level']}")
print(f"屏蔽文本: {result['masked_text']}")
```

## 🔒 安全特性

### 1. 加密存储
- 敏感词使用AES-128加密存储
- 基于PBKDF2-HMAC-SHA256密钥派生
- 100,000次迭代增强安全性

### 2. 无敏感词泄露
- 代码中不包含任何敏感词明文
- 加密数据无法被逆向破解
- 即使获取文件也无法读取敏感词

### 3. 密码保护
- 需要密码才能解密敏感词
- 密码不在代码中存储
- 支持自定义密码

## 📁 文件说明

| 文件 | 用途 | 是否包含敏感词 |
|---|---|---|
| `encrypt_sensitive_words.py` | 加密工具 | ❌ 无敏感词 |
| `encrypted_content_moderator.py` | 加密审核器核心 | ❌ 无敏感词 |
| `safe_content_moderator.py` | 安全包装器 | ❌ 无敏感词 |
| `encrypted_sensitive_words.json` | 加密敏感词数据 | ✅ 已加密 |

## ⚙️ 配置选项

### 自定义密码
在创建审核器时指定密码：

```python
# 使用自定义密码
moderator = SafeContentModerator(password="your_custom_password")
```

### 更换敏感词
1. 重新运行加密工具
2. 输入新的敏感词列表
3. 替换 `encrypted_sensitive_words.json` 文件

## 🧪 测试示例

```python
# 测试加密审核器
from safe_content_moderator import SafeContentModerator

moderator = SafeContentModerator()
result = moderator.check_text("测试内容")
print(result)
```

## 🔍 系统信息查询

```python
# 查看系统状态
info = moderator.get_system_info()
print(json.dumps(info, indent=2))
```

## 📞 技术支持

### 常见问题

**Q: 忘记加密密码怎么办？**
A: 需要重新运行加密工具生成新的加密文件

**Q: 如何添加新的敏感词？**
A: 重新运行加密工具，包含所有敏感词（新旧一起）

**Q: 加密文件损坏了怎么办？**
A: 使用备份的加密文件或重新加密敏感词

**Q: 如何验证加密是否成功？**
A: 使用加密工具的验证功能或检查加密文件内容

## 🚨 安全警告

1. **密码安全**: 使用强密码并妥善保管
2. **文件备份**: 定期备份加密敏感词文件
3. **权限控制**: 限制加密文件的访问权限
4. **定期更新**: 定期更新敏感词列表和密码

## ✅ 部署检查清单

- [ ] 已使用加密工具生成敏感词文件
- [ ] 已测试加密审核器功能
- [ ] 已设置安全的加密密码
- [ ] 已备份加密敏感词文件
- [ ] 已配置应用使用加密审核器
- [ ] 已测试生产环境功能

## 🎯 一键部署命令

```bash
# 1. 加密敏感词
python encrypt_sensitive_words.py

# 2. 测试审核功能
python -c "from safe_content_moderator import check_text_safe; print(check_text_safe('测试内容'))"

# 3. 部署到服务器
# 上传所有.py文件和encrypted_sensitive_words.json
```

---

**注意**: 本系统专为服务器安全设计，敏感词全程加密，无需担心被平台检测或封禁。