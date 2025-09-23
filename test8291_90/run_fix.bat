@echo off
echo 正在修复数据库外键约束...
echo.

REM 检查是否安装了MySQL
where mysql >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: MySQL未安装或未添加到系统PATH
    echo 请手动运行以下SQL命令:
    echo.
    type fix_db_step_by_step.sql
    pause
    exit /b 1
)

echo 使用Python脚本修复...
python run_mysql_fix.py

echo.
echo 修复完成！
pause