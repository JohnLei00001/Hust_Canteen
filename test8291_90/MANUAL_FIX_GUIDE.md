# 数据库外键约束修复指南

## 问题描述
错误：`1452 (23000): Cannot add or update a child row: a foreign key constraint fails`

原因：`dish_reviews.stall_dish_id` 被错误地定义为外键，引用了 `dishes.dish_id`，但应该引用 `stall_dishes.id`。

## 修复步骤

### 方法1：使用Python脚本自动修复
1. 确保已安装Python和mysql-connector-python
2. 运行：
   ```bash
   python run_mysql_fix.py
   ```

### 方法2：手动MySQL命令修复

#### 步骤1：登录MySQL
```bash
mysql -u root -pRay123_123 hust_canteen
```

#### 步骤2：查看当前约束
```sql
SHOW CREATE TABLE dish_reviews;
```

#### 步骤3：删除错误约束
找到约束名称（通常是 `dish_reviews_ibfk_2` 或其他），然后：
```sql
ALTER TABLE dish_reviews DROP FOREIGN KEY 约束名称;
```

#### 步骤4：添加正确约束
```sql
ALTER TABLE dish_reviews 
ADD CONSTRAINT fk_dish_reviews_stall_dish 
FOREIGN KEY (stall_dish_id) REFERENCES stall_dishes(id) 
ON DELETE CASCADE 
ON UPDATE CASCADE;
```

### 方法3：使用SQL文件
```bash
mysql -u root -pRay123_123 hust_canteen < fix_db_step_by_step.sql
```

## 验证修复
运行以下SQL验证：
```sql
SELECT 
    CONSTRAINT_NAME, 
    COLUMN_NAME, 
    REFERENCED_TABLE_NAME, 
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_SCHEMA = 'hust_canteen' 
AND TABLE_NAME = 'dish_reviews'
AND REFERENCED_TABLE_NAME IS NOT NULL;
```

## 预期结果
修复后，`stall_dish_id` 应该引用 `stall_dishes.id` 而不是 `dishes.dish_id`。