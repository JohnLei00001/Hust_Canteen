#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库性能优化执行脚本
运行此脚本可以创建所有必要的索引来优化查询性能
"""

import mysql.connector
from mysql.connector import Error
import time

def create_optimized_indexes():
    """创建优化的数据库索引"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='your_pswd',
            database='hust_canteen'
        )
        
        cursor = conn.cursor()
        
        print("开始数据库性能优化...")
        start_time = time.time()
        
        # 索引创建语句列表
        indexes = [
            # 菜品相关索引
            "CREATE INDEX idx_dishes_rating ON dishes(avg_rating)",
            "CREATE INDEX idx_dishes_review_count ON dishes(review_count)",
            "CREATE INDEX idx_dishes_name ON dishes(name)",
            
            # 食堂相关索引
            "CREATE INDEX idx_canteens_crowd_level ON canteens(crowd_level)",
            "CREATE INDEX idx_canteens_name ON canteens(name)",
            
            # 窗口相关索引
            "CREATE INDEX idx_canteen_stalls_queue_rating ON canteen_stalls(queue_rating)",
            "CREATE INDEX idx_canteen_stalls_canteen_id ON canteen_stalls(canteen_id)",
            "CREATE INDEX idx_canteen_stalls_name ON canteen_stalls(custom_name)",
            
            # 菜品供应相关索引
            "CREATE INDEX idx_stall_dishes_available ON stall_dishes(is_available)",
            "CREATE INDEX idx_stall_dishes_dish_id ON stall_dishes(dish_id)",
            "CREATE INDEX idx_stall_dishes_stall_id ON stall_dishes(stall_id)",
            
            # 窗口类型索引
            "CREATE INDEX idx_stall_types_name ON stall_types(name)",
            
            # 评论相关索引
            "CREATE INDEX idx_dish_reviews_user_id ON dish_reviews(user_id)",
            "CREATE INDEX idx_dish_reviews_stall_dish_id ON dish_reviews(stall_dish_id)",
            "CREATE INDEX idx_dish_reviews_created_at ON dish_reviews(created_at)",
            
            # 收藏相关索引
            "CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id)",
            "CREATE INDEX idx_user_favorites_stall_dish_id ON user_favorites(stall_dish_id)",
            "CREATE INDEX idx_user_favorites_created_at ON user_favorites(created_at)"
        ]
        
        created_count = 0
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                conn.commit()
                print(f"✓ 创建索引成功: {index_sql}")
                created_count += 1
            except Error as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e) or "Duplicate index" in str(e):
                    print(f"○ 索引已存在: {index_sql}")
                else:
                    print(f"✗ 创建索引失败: {index_sql} - {e}")
        
        # 分析表统计信息
        print("\n更新表统计信息...")
        tables = ['dishes', 'canteens', 'canteen_stalls', 'stall_dishes', 'stall_types', 'dish_reviews', 'user_favorites']
        for table in tables:
            try:
                cursor.execute(f"ANALYZE TABLE {table}")
                print(f"✓ 已分析表: {table}")
            except Error as e:
                print(f"✗ 分析表失败: {table} - {e}")
        
        elapsed_time = time.time() - start_time
        print(f"\n数据库优化完成！")
        print(f"创建了 {created_count} 个新索引")
        print(f"总耗时: {elapsed_time:.2f} 秒")
        
        # 显示当前索引信息
        print("\n当前数据库索引概览:")
        for table in tables:
            try:
                cursor.execute(f"SHOW INDEX FROM {table}")
                indexes = cursor.fetchall()
                print(f"{table}: {len(indexes)} 个索引")
            except Error as e:
                print(f"{table}: 获取索引信息失败 - {e}")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"数据库连接错误: {e}")
        if 'conn' in locals():
            conn.close()

def check_query_performance():
    """检查关键查询的性能"""
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Ray123_123',
            database='hust_canteen'
        )
        
        cursor = conn.cursor()
        
        print("\n检查关键查询性能...")
        
        # 测试推荐查询性能
        test_queries = [
            "推荐菜品查询",
            """
            SELECT d.dish_id, d.name, d.avg_rating 
            FROM dishes d
            JOIN stall_dishes sd ON d.dish_id = sd.dish_id
            WHERE sd.is_available = 1 
            ORDER BY d.avg_rating DESC 
            LIMIT 10
            """,
            
            "搜索查询",
            """
            SELECT d.dish_id, d.name, d.avg_rating
            FROM dishes d
            WHERE d.name LIKE '%测试%'
            ORDER BY d.avg_rating DESC
            LIMIT 20
            """
        ]
        
        for i in range(0, len(test_queries), 2):
            query_name = test_queries[i]
            query_sql = test_queries[i+1]
            
            try:
                start_time = time.time()
                cursor.execute("EXPLAIN " + query_sql)
                explain_result = cursor.fetchall()
                
                cursor.execute(query_sql)
                cursor.fetchall()
                elapsed_time = (time.time() - start_time) * 1000
                
                print(f"\n{query_name}:")
                print(f"  执行时间: {elapsed_time:.2f}ms")
                print(f"  执行计划: {len(explain_result)} 行")
                
            except Error as e:
                print(f"{query_name}: 测试失败 - {e}")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"性能检查错误: {e}")

if __name__ == "__main__":
    print("=== 食堂系统数据库性能优化工具 ===")
    print("此脚本将创建优化的数据库索引以提升查询性能")
    print("")
    
    create_optimized_indexes()
    check_query_performance()
    
    print("\n=== 优化完成 ===")
    print("建议重启应用以使优化生效")
