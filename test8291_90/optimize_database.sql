-- 数据库性能优化脚本
-- 为常用查询字段添加索引

USE hust_canteen;

-- 1. 优化推荐查询的索引
-- 菜品推荐相关索引
CREATE INDEX IF NOT EXISTS idx_dishes_rating ON dishes(avg_rating);
CREATE INDEX IF NOT EXISTS idx_dishes_review_count ON dishes(review_count);
CREATE INDEX IF NOT EXISTS idx_stall_dishes_available ON stall_dishes(is_available);
CREATE INDEX IF NOT EXISTS idx_stall_dishes_dish_id ON stall_dishes(dish_id);
CREATE INDEX IF NOT EXISTS idx_stall_dishes_stall_id ON stall_dishes(stall_id);

-- 食堂拥挤度索引
CREATE INDEX IF NOT EXISTS idx_canteens_crowd_level ON canteens(crowd_level);

-- 窗口排队评分索引
CREATE INDEX IF NOT EXISTS idx_canteen_stalls_queue_rating ON canteen_stalls(queue_rating);
CREATE INDEX IF NOT EXISTS idx_canteen_stalls_canteen_id ON canteen_stalls(canteen_id);

-- 2. 优化搜索查询的索引
-- 菜品名称索引
CREATE INDEX IF NOT EXISTS idx_dishes_name ON dishes(name);

-- 食堂名称索引
CREATE INDEX IF NOT EXISTS idx_canteens_name ON canteens(name);

-- 窗口名称索引
CREATE INDEX IF NOT EXISTS idx_canteen_stalls_name ON canteen_stalls(custom_name);
CREATE INDEX IF NOT EXISTS idx_stall_types_name ON stall_types(name);

-- 3. 优化外键索引
CREATE INDEX IF NOT EXISTS idx_dish_reviews_user_id ON dish_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_dish_reviews_stall_dish_id ON dish_reviews(stall_dish_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_user_favorites_stall_dish_id ON user_favorites(stall_dish_id);

-- 4. 优化排行榜查询索引
-- 收藏数统计索引
CREATE INDEX IF NOT EXISTS idx_user_favorites_stall_dish_id_count ON user_favorites(stall_dish_id);

-- 5. 检查并优化现有索引
SHOW INDEX FROM dishes;
SHOW INDEX FROM canteens;
SHOW INDEX FROM canteen_stalls;
SHOW INDEX FROM stall_dishes;
SHOW INDEX FROM dish_reviews;
SHOW INDEX FROM user_favorites;

-- 6. 分析查询性能
-- 运行以下命令来查看查询执行计划
EXPLAIN SELECT d.dish_id, d.name, d.avg_rating 
FROM dishes d 
JOIN stall_dishes sd ON d.dish_id = sd.dish_id 
WHERE sd.is_available = 1 
ORDER BY d.avg_rating DESC 
LIMIT 10;