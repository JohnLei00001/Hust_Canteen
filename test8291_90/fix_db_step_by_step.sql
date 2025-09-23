-- 步骤1：查看当前表结构和外键约束
USE hust_canteen;

SHOW CREATE TABLE dish_reviews;

-- 步骤2：删除错误的外键约束
-- 注意：需要根据SHOW CREATE TABLE的结果确定正确的约束名称
-- 如果约束名称是 dish_reviews_ibfk_2：
ALTER TABLE dish_reviews DROP FOREIGN KEY dish_reviews_ibfk_2;

-- 步骤3：添加正确的外键约束
ALTER TABLE dish_reviews 
ADD CONSTRAINT fk_dish_reviews_stall_dish 
FOREIGN KEY (stall_dish_id) REFERENCES stall_dishes(id) 
ON DELETE CASCADE 
ON UPDATE CASCADE;