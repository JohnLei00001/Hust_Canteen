-- 修复 dish_reviews 表的外键约束问题
-- 错误：stall_dish_id 引用了 dishes.dish_id
-- 正确：stall_dish_id 应该引用 stall_dishes.id

-- 首先删除错误的外键约束
ALTER TABLE dish_reviews DROP FOREIGN KEY dish_reviews_ibfk_2;

-- 然后添加正确的外键约束
ALTER TABLE dish_reviews 
ADD CONSTRAINT fk_dish_reviews_stall_dish 
FOREIGN KEY (stall_dish_id) 
REFERENCES stall_dishes(id) 
ON DELETE CASCADE 
ON UPDATE CASCADE;