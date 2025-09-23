-- 快速修复：删除错误的外键约束
USE hust_canteen;

-- 删除错误的外键约束（引用dishes.dish_id）
ALTER TABLE dish_reviews DROP FOREIGN KEY dish_reviews_ibfk_2;

-- 验证修复结果
SHOW CREATE TABLE dish_reviews;