#!/usr/bin/env python3
"""
安全启动脚本 - 校园食堂系统
包含安全检查和生产环境配置
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/startup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityChecker:
    """安全检查器"""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
    
    def add_check(self, name, func):
        """添加安全检查"""
        self.checks.append((name, func))
    
    def run_checks(self):
        """运行所有安全检查"""
        logger.info("开始安全检查...")
        
        for name, check_func in self.checks:
            try:
                result = check_func()
                if result is True:
                    logger.info(f"✅ {name}")
                elif result is False:
                    logger.warning(f"⚠️  {name}")
                    self.warnings.append(name)
                else:
                    logger.error(f"❌ {name}: {result}")
                    self.errors.append(f"{name}: {result}")
            except Exception as e:
                logger.error(f"❌ {name}: {str(e)}")
                self.errors.append(f"{name}: {str(e)}")
        
        logger.info(f"安全检查完成 - 警告: {len(self.warnings)}, 错误: {len(self.errors)}")
        return len(self.errors) == 0

def check_secret_key():
    """检查SECRET_KEY配置"""
    try:
        from app import app
        if app.secret_key == 'your_key':
            return "使用了默认SECRET_KEY，请更改为安全的密钥"
        return True
    except:
        return "无法检查SECRET_KEY配置"

def check_debug_mode():
    """检查DEBUG模式"""
    try:
        from app import app
        if app.debug:
            return False  # 警告：生产环境不应启用DEBUG
        return True
    except:
        return "无法检查DEBUG模式"

def check_database_security():
    """检查数据库安全配置"""
    try:
        from app import db_config
        if db_config['host'] == 'localhost' and db_config['user'] == 'root':
            return False  # 警告：使用root用户
        return True
    except:
        return "无法检查数据库配置"

def check_ssl_configuration():
    """检查SSL配置"""
    # 检查是否配置了HTTPS
    cert_files = [
        'cert.pem',
        'fullchain.pem',
        'privkey.pem'
    ]
    
    found_certs = [f for f in cert_files if os.path.exists(f)]
    if len(found_certs) >= 2:
        return True
    return False  # 警告：未找到SSL证书

def check_file_permissions():
    """检查文件权限"""
    sensitive_files = [
        'app.py',
        'security_config.py',
        'logs/',
        'static/uploads/'
    ]
    
    issues = []
    for item in sensitive_files:
        if os.path.exists(item):
            stat = os.stat(item)
            # 检查文件是否过于开放
            if stat.st_mode & 0o077:
                issues.append(f"{item} 权限过于开放")
    
    return True if not issues else f"文件权限问题: {', '.join(issues)}"

def check_dependencies():
    """检查依赖包安全性"""
    try:
        import pkg_resources
        vulnerable_packages = [
            'flask',
            'mysql-connector-python',
            'bcrypt'
        ]
        
        outdated = []
        for package in vulnerable_packages:
            try:
                dist = pkg_resources.get_distribution(package)
                # 这里可以添加版本检查逻辑
                outdated.append(f"{package}=={dist.version}")
            except pkg_resources.DistributionNotFound:
                continue
        
        return True if not outdated else f"需要更新: {', '.join(outdated)}"
    except:
        return "无法检查依赖包"

def check_environment_variables():
    """检查环境变量"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        return f"缺少环境变量: {', '.join(missing)}"
    return True

def check_log_configuration():
    """检查日志配置"""
    log_dir = Path('logs')
    if not log_dir.exists():
        log_dir.mkdir(exist_ok=True)
        return False  # 警告：日志目录不存在，已创建
    
    # 检查日志文件权限
    try:
        test_file = log_dir / 'test.log'
        test_file.touch()
        test_file.unlink()
        return True
    except:
        return "日志目录权限问题"

def check_backup_configuration():
    """检查备份配置"""
    backup_dir = Path('backups')
    if not backup_dir.exists():
        return False  # 警告：备份目录不存在
    return True

def create_secure_startup_script():
    """创建安全启动脚本"""
    
    # 创建必要的目录
    directories = ['logs', 'backups', 'security']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # 创建安全启动脚本
    startup_script = """
#!/bin/bash
# 安全启动脚本

echo "启动校园食堂系统安全检查..."

# 检查Python环境
python3 --version || { echo "Python 3未安装"; exit 1; }

# 检查依赖
pip3 install -r requirements.txt

# 设置安全环境变量
export FLASK_ENV=production
export FLASK_DEBUG=0

# 启动安全检查
python3 -c "
from secure_start import run_security_check
if run_security_check():
    print('安全检查通过，启动应用...')
    import subprocess
    subprocess.run(['python3', 'start_production_windows.py'])
else:
    print('安全检查未通过，请修复问题后重试')
    exit(1)
"
"""
    
    with open('secure_start.sh', 'w') as f:
        f.write(startup_script)
    
    # 设置执行权限
    os.chmod('secure_start.sh', 0o755)
    
    logger.info("安全启动脚本已创建: secure_start.sh")

def run_security_check():
    """运行完整的安全检查"""
    checker = SecurityChecker()
    
    # 添加所有安全检查
    checker.add_check("SECRET_KEY配置", check_secret_key)
    checker.add_check("DEBUG模式", check_debug_mode)
    checker.add_check("数据库安全", check_database_security)
    checker.add_check("SSL配置", check_ssl_configuration)
    checker.add_check("文件权限", check_file_permissions)
    checker.add_check("依赖包安全", check_dependencies)
    checker.add_check("环境变量", check_environment_variables)
    checker.add_check("日志配置", check_log_configuration)
    checker.add_check("备份配置", check_backup_configuration)
    
    # 运行检查
    success = checker.run_checks()
    
    if success:
        logger.info("✅ 所有安全检查通过，可以启动应用")
        return True
    else:
        logger.error("❌ 安全检查未通过，请修复以下问题:")
        for error in checker.errors:
            logger.error(f"  - {error}")
        
        if checker.warnings:
            logger.warning("⚠️  警告项:")
            for warning in checker.warnings:
                logger.warning(f"  - {warning}")
        
        return False

if __name__ == "__main__":
    print("🔐 校园食堂系统安全启动检查")
    print("=" * 50)
    
    # 运行安全检查
    if run_security_check():
        print("\n🚀 启动应用...")
        try:
            from start_production_windows import main
            main()
        except ImportError:
            print("请使用: python start_production_windows.py 启动应用")
    else:
        print("\n❌ 请先修复安全问题，然后重试")
        sys.exit(1)
