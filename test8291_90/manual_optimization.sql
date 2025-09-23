-- 食堂系统数据库性能优化脚本
-- 手动执行这些SQL语句来优化查询性能

-- 查看当前索引
SHOW INDEX FROM dishes;
SHOW INDEX FROM canteens;
SHOW INDEX FROM canteen_stalls;
SHOW INDEX FROM stall_dishes;
SHOW INDEX FROM dish_reviews;
SHOW INDEX FROM user_favorites;

-- 创建菜品相关索引
CREATE INDEX idx_dishes_rating ON dishes(avg_rating);
CREATE INDEX idx_dishes_review_count ON dishes(review_count);
CREATE INDEX idx_dishes_name ON dishes(name);

-- 创建食堂相关索引
CREATE INDEX idx_canteens_crowd_level ON canteens(crowd_level);
CREATE INDEX idx_canteens_name ON canteens(name);

-- 创建窗口相关索引
CREATE INDEX idx_canteen_stalls_queue_rating ON canteen_stalls(queue_rating);
CREATE INDEX idx_canteen_stalls_canteen_id ON canteen_stalls(canteen_id);
CREATE INDEX idx_canteen_stalls_name ON canteen_stalls(custom_name);

-- 创建菜品供应相关索引
CREATE INDEX idx_stall_dishes_available ON stall_dishes(is_available);
CREATE INDEX idx_stall_dishes_dish_id ON stall_dishes(dish_id);
CREATE INDEX idx_stall_dishes_stall_id ON stall_dishes(stall_id);

-- 创建评论相关索引
CREATE INDEX idx_dish_reviews_user_id ON dish_reviews(user_id);
CREATE INDEX idx_dish_reviews_stall_dish_id ON dish_reviews(stall_dish_id);
CREATE INDEX idx_dish_reviews_created_at ON dish_reviews(created_at);

-- 创建收藏相关索引
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_stall_dish_id ON user_favorites(stall_dish_id);
CREATE INDEX idx_user_favorites_created_at ON user_favorites(created_at);

-- 分析表统计信息
ANALYZE TABLE dishes;
ANALYZE TABLE canteens;
ANALYZE TABLE canteen_stalls;
ANALYZE TABLE stall_dishes;
ANALYZE TABLE dish_reviews;
ANALYZE TABLE user_favorites;

-- 测试查询性能
EXPLAIN SELECT d.dish_id, d.name, d.avg_rating 
FROM dishes d
JOIN stall_dishes sd ON d.dish_id = sd.dish_id
WHERE sd.is_available = 1 
ORDER BY d.avg_rating DESC 
LIMIT 10;

-- 如果索引已存在，可以先删除再创建
-- DROP INDEX idx_dishes_rating ON dishes;
-- DROP INDEX idx_dishes_review_count ON dishes;
-- DROP INDEX idx_dishes_name ON dishes;
-- 其他索引类似...然后重新创建